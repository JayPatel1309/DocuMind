# DocuMind

DocuMind is an AI-powered document classification and intelligent indexing system. It provides an end-to-end pipeline for uploading, processing, classifying, and searching through large volumes of documents using machine learning and natural language processing.

## Architecture and Features

The system consists of a FastAPI backend and a minimal, vanilla JavaScript frontend.

### 1. Document Processing Pipeline
When a PDF is uploaded, the system performs the following automated steps:
- Text Extraction: Uses PyMuPDF to extract raw text from the document.
- Intelligent Classification: A custom-trained Logistic Regression model analyzes the text and assigns it to one of six categories (Finance, HR, Legal, Contracts, Technical, Other).
- Summarization and Entity Extraction: Uses SpaCy to extract key topics and generate a concise summary of the document.
- Semantic Chunking: The document is split into sentence-based chunks for precise information retrieval.

### 2. Semantic Vector Search
- Embedding Generation: Each text chunk is converted into a high-dimensional vector using a local SentenceTransformer model.
- Vector Database: The embeddings are indexed using FAISS (Facebook AI Similarity Search), allowing for ultra-fast, context-aware semantic search queries rather than basic keyword matching.

### 3. Role-Based Access Control (RBAC)
The system includes built-in security to restrict sensitive documents:
- Admin Role: Can view, search, and download all documents across the system.
- Standard Role: Cannot view, search, or access documents classified under the "Legal" or "Contracts" categories. These documents are dynamically filtered from the dashboard, statistics, and vector search results.

## Technology Stack

- Backend Framework: FastAPI (Python)
- Database: PostgreSQL
- Machine Learning Models: Scikit-learn (Logistic Regression), SentenceTransformers, SpaCy
- Vector Search: FAISS
- Frontend: HTML5, CSS3, Vanilla JavaScript (Single Page Application)

## Setup and Installation

1. Clone the repository and navigate to the project directory.
   Note: The repository uses Git Large File Storage (Git LFS) for machine learning models. Ensure you have Git LFS installed and run `git lfs pull` to download the models.

2. Set up the PostgreSQL database:
   - Create a database named `DocuMind`.
   - Execute the SQL schema to create the necessary tables (`categories`, `documents`, `document_metadata`, `document_chunks`, `users`).
   - Update the database credentials in `backend/database/connection.py` and `backend/database/rbac.py` if your local Postgres setup uses different credentials.

3. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the application:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```

5. Access the application:
   Open a web browser and navigate to `http://127.0.0.1:8000`. 

## API Endpoints

- `POST /api/login`: Authenticates a user and returns session information.
- `GET /api/stats`: Returns system statistics (total documents, category distributions), filtered by the user's role.
- `GET /api/categories`: Returns a list of available document categories.
- `GET /api/documents`: Returns a list of processed documents with their metadata.
- `GET /api/documents/{id}`: Returns detailed information for a specific document.
- `GET /api/documents/{id}/view`: Streams the original PDF file to the client.
- `POST /api/upload`: Accepts a PDF file upload and triggers the machine learning processing pipeline.
- `POST /api/search`: Performs a FAISS-backed semantic search across all authorized document chunks.
