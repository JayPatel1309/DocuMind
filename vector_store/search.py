import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.database.dataentry import fetch_document_chunk
from sklearn.metrics.pairwise import cosine_similarity
import faiss
embedder=SentenceTransformer(r"P:\AI-Powered Document Classification and Intelligent Indexing\ml\models\sentence_transformer_model")
def query_parser(query):
    query_vector = embedder.encode([query])
    query_vector = np.array(query_vector).astype('float32')
    index=faiss.read_index(r'P:\AI-Powered Document Classification and Intelligent Indexing\vector_store\global_vector_index.faiss')
    distances,indexes=index.search(query_vector,5)
    print(indexes)
def output_generator(indexes):
    chunk_list=[]
    for index in indexes:
        chunk_list.append(fetch_document_chunk(index))
    chunk_string=" ".join(chunk_list)
    return chunk_string

print(output_generator(query_parser("employment rates")))
