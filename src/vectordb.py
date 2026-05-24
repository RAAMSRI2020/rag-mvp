from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from config import QDRANT_PATH, COLLECTION_NAME
from src.embedder import get_embedding_dim

_client = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(path=QDRANT_PATH)
    return _client


def close_client() -> None:
    global _client
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
        _client = None


def ensure_collection() -> None:
    client = get_client()
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=get_embedding_dim(),
                distance=Distance.COSINE
            )
        )


def upsert_snippets(
    snippets: list[dict],
    embeddings: list[list[float]],
    session_id: str,
    source_pdf: str
) -> None:
    client = get_client()
    points = []

    for snippet, embedding in zip(snippets, embeddings):
        point = PointStruct(
            id=hash(f"{session_id}-{snippet['turn_start']}-{snippet['turn_end']}-{source_pdf}-{snippet['text'][:100]}") & 0x7FFFFFFF,
            vector=embedding,
            payload={
                "session_id": session_id,
                "source_pdf": source_pdf,
                "turn_start": snippet["turn_start"],
                "turn_end": snippet["turn_end"],
                "text": snippet["text"],
            }
        )
        points.append(point)

    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)


def search_similar(query_vector: list[float], limit: int = 10) -> list[dict]:
    client = get_client()

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit
    ).points

    docs = []
    for result in results:
        docs.append({
            "score": result.score,
            "session_id": result.payload["session_id"],
            "source_pdf": result.payload["source_pdf"],
            "turn_start": result.payload["turn_start"],
            "turn_end": result.payload["turn_end"],
            "text": result.payload["text"],
        })

    return docs