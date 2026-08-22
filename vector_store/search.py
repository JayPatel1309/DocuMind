import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.database.dataentry import fetch_document_chunk
from sklearn.metrics.pairwise import cosine_similarity
import faiss

embedder = SentenceTransformer(r"P:\AI-Powered Document Classification and Intelligent Indexing\ml\models\sentence_transformer_model")


def query_parser(query, top_k=5):
    query_vector = embedder.encode([query])
    query_vector = np.array(query_vector).astype('float32')
    index = faiss.read_index(r'P:\AI-Powered Document Classification and Intelligent Indexing\vector_store\global_vector_index.faiss')
    distances, indexes = index.search(query_vector, top_k)
    return indexes[0].tolist(), distances[0].tolist()


def output_generator(indexes):
    chunk_list = []
    for index in indexes:
        chunk = fetch_document_chunk(int(index))
        if chunk is not None:
            chunk_list.append(chunk)
    chunk_string = " ".join(chunk_list)
    return chunk_string


def search(query: str, top_k: int = 5) -> list[dict]:
    indexes, distances = query_parser(query, top_k=top_k)
    results = []
    for index, distance in zip(indexes, distances):
        chunk = fetch_document_chunk(int(index))
        if chunk is not None:
            results.append({
                "chunk_text": chunk,
                "score": float(distance)
            })
    return results
