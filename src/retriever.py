from config import TOP_K
from src.embedder import embed_query
from src.vectordb import search_similar


def retrieve_top_k(query: str, k: int = TOP_K) -> list[dict]:
    query_vector = embed_query(query)
    return search_similar(query_vector=query_vector, limit=k)