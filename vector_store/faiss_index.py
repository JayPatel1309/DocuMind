import faiss
from sentence_transformers import SentenceTransformer
import pandas as pd
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity


def faiss_index(file_name_chunk,text_sample,embedder):
    text_embedding = embedder.encode([text_sample], normalize_embeddings=True)
    text_embedding = np.array(text_embedding).astype('float32')
    if os.path.exists(file_name_chunk):
        index=faiss.read_index(file_name_chunk)
    else:
        dimension=text_embedding.shape[1]
        index=faiss.IndexFlatIP(dimension)
    index.add(text_embedding)
    faiss.write_index(index, file_name_chunk)
    new_faiss_id = index.ntotal - 1
    return new_faiss_id


