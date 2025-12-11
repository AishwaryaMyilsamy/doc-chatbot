# app/embeddings.py
from sentence_transformers import SentenceTransformer

# Initialize a lightweight model (384 dims)
model = SentenceTransformer("all-MiniLM-L12-v2")

def get_embedding(text: str) -> list[float]:
    """
    Converts a text string into a vector embedding.
    Returns a list of floats (384 dimensions).
    """
    embedding = model.encode(text)
    return embedding.tolist()
