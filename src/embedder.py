from sentence_transformers import SentenceTransformer
from config import EMBED_MODEL

_model = SentenceTransformer(EMBED_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    embeddings = _model.encode(texts, normalize_embeddings=True)
    return [embedding.tolist() for embedding in embeddings]


def embed_query(query: str) -> list[float]:
    embedding = _model.encode([query], normalize_embeddings=True)[0]
    return embedding.tolist()


def get_embedding_dim() -> int:
    return len(_model.encode(["test"])[0])