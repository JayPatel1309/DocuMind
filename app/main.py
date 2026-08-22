from fastapi import Depends, FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
import shutil
import os

from backend.database.connection import Base, engine, get_db
from backend.database.rbac import authenticate_user, is_authorized_to_view

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DocuMind API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "uploads")
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")


# --- Request Models ---
class LoginRequest(BaseModel):
    username: str
    password: str


class SearchRequest(BaseModel):
    query: str


# --- Serve Frontend ---
@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# --- API: Login ---
@app.post("/api/login")
def login(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"token": user["username"], "role": user["role"]}


# --- API: Categories ---
@app.get("/api/categories")
def get_categories(
    x_username: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    rows = db.execute(text("SELECT * FROM categories")).mappings().all()
    results = []
    for row in rows:
        r = dict(row)
        if is_authorized_to_view(x_username, r.get("category_name")):
            results.append(r)
    return results


# --- API: Stats ---
@app.get("/api/stats")
def get_stats(
    x_username: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    cat_rows = db.execute(text("SELECT category_id, category_name FROM categories")).mappings().all()
    authorized_categories = [
        row["category_name"] for row in cat_rows
        if is_authorized_to_view(x_username, row["category_name"])
    ]

    doc_rows = db.execute(text(
        "SELECT d.document_id, c.category_name, d.classification_confidence "
        "FROM documents d "
        "LEFT JOIN categories c ON d.category_id = c.category_id"
    )).mappings().all()

    category_distribution = {cat: 0 for cat in authorized_categories}
    confidences = []
    total_docs = 0

    for doc in doc_rows:
        cat_name = doc.get("category_name")
        if is_authorized_to_view(x_username, cat_name):
            total_docs += 1
            if cat_name in category_distribution:
                category_distribution[cat_name] += 1
            elif cat_name:
                category_distribution[cat_name] = 1
            if doc.get("classification_confidence") is not None:
                confidences.append(float(doc["classification_confidence"]))

    total_categories = len(authorized_categories)
    avg_confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0.0

    return {
        "total_documents": total_docs,
        "total_categories": total_categories,
        "avg_confidence": avg_confidence,
        "category_distribution": category_distribution,
    }


# --- API: List Documents ---
@app.get("/api/documents")
def get_documents(
    x_username: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    rows = db.execute(text(
        "SELECT d.document_id, d.filename, c.category_name, "
        "d.classification_confidence, d.upload_date, d.processing_status "
        "FROM documents d "
        "LEFT JOIN categories c ON d.category_id = c.category_id "
        "ORDER BY d.classification_confidence DESC, d.document_id DESC"
    )).mappings().all()
    results = []
    for row in rows:
        r = dict(row)
        if is_authorized_to_view(x_username, r.get("category_name")):
            if r.get("classification_confidence") is not None:
                r["classification_confidence"] = float(r["classification_confidence"])
            if r.get("upload_date") is not None:
                r["upload_date"] = str(r["upload_date"])
            results.append(r)
    return results


# --- API: Single Document Detail ---
@app.get("/api/documents/{doc_id}")
def get_document_detail(
    doc_id: int,
    x_username: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    doc_row = db.execute(text(
        "SELECT d.document_id, d.filename, c.category_name, "
        "d.classification_confidence, d.upload_date, d.processing_status, "
        "d.file_type, d.file_size "
        "FROM documents d "
        "LEFT JOIN categories c ON d.category_id = c.category_id "
        "WHERE d.document_id = :doc_id"
    ), {"doc_id": doc_id}).mappings().first()

    if not doc_row:
        raise HTTPException(status_code=404, detail="Document not found")

    result = dict(doc_row)
    if not is_authorized_to_view(x_username, result.get("category_name")):
        raise HTTPException(status_code=403, detail="Access denied")

    if result.get("classification_confidence") is not None:
        result["classification_confidence"] = float(result["classification_confidence"])
    if result.get("upload_date") is not None:
        result["upload_date"] = str(result["upload_date"])

    # Fetch metadata
    meta_row = db.execute(text(
        "SELECT title, author, document_date, summary, key_topics "
        "FROM document_metadata WHERE document_id = :doc_id"
    ), {"doc_id": doc_id}).mappings().first()

    if meta_row:
        meta = dict(meta_row)
        if meta.get("document_date") is not None:
            meta["document_date"] = str(meta["document_date"])
        result.update(meta)
    else:
        result.update({"title": None, "author": None, "document_date": None, "summary": None, "key_topics": None})

    return result


# --- API: View/Download Document ---
@app.get("/api/documents/{doc_id}/view")
def view_document(
    doc_id: int,
    x_username: Optional[str] = Header(None),
    user: Optional[str] = None,
    db: Session = Depends(get_db)
):
    actual_user = user or x_username
    doc_row = db.execute(text(
        "SELECT d.file_path, c.category_name "
        "FROM documents d "
        "LEFT JOIN categories c ON d.category_id = c.category_id "
        "WHERE d.document_id = :doc_id"
    ), {"doc_id": doc_id}).mappings().first()

    if not doc_row:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if not is_authorized_to_view(actual_user, doc_row["category_name"]):
        raise HTTPException(status_code=403, detail="Not authorized to view this document")
        
    file_path = doc_row["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
        
    return FileResponse(file_path, media_type="application/pdf", filename=os.path.basename(file_path))


# --- Lazy-loaded search dependencies ---
_search_embedder = None
_FAISS_INDEX_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "vector_store", "global_vector_index.faiss"
)
_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ml", "models", "sentence_transformer_model"
)


def _get_search_embedder():
    global _search_embedder
    if _search_embedder is None:
        from sentence_transformers import SentenceTransformer
        _search_embedder = SentenceTransformer(_MODEL_PATH)
    return _search_embedder


# --- API: Semantic Search ---
@app.post("/api/search")
def search_documents(
    request: SearchRequest,
    x_username: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        import faiss
        import numpy as np

        embedder = _get_search_embedder()
        query_vector = embedder.encode([request.query])
        query_vector = np.array(query_vector).astype('float32')

        index = faiss.read_index(_FAISS_INDEX_PATH)
        distances, indexes = index.search(query_vector, 5)

        results = []
        for idx, dist in zip(indexes[0].tolist(), distances[0].tolist()):
            if idx < 0:
                continue
            row = db.execute(
                text(
                    "SELECT c.chunk_text, cat.category_name, d.filename, d.document_id "
                    "FROM document_chunks c "
                    "JOIN documents d ON c.document_id = d.document_id "
                    "JOIN categories cat ON d.category_id = cat.category_id "
                    "WHERE c.embedding_id = :eid"
                ),
                {"eid": idx}
            ).mappings().first()
            if row:
                if is_authorized_to_view(x_username, row["category_name"]):
                    results.append({
                        "chunk_text": row["chunk_text"],
                        "score": round(float(dist), 4),
                        "filename": row["filename"],
                        "document_id": row["document_id"]
                    })

        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- API: Upload PDF ---
@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Save uploaded file
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        from document_processing.extractor import process_pdf
        result = process_pdf(file_path)
        # Convert key_topics list to string for JSON response
        if isinstance(result.get("key_topics"), list):
            result["key_topics"] = result["key_topics"]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))