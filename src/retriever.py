import re
from config import TOP_K, RETRIEVE_K
from src.embedder import embed_query
from src.vectordb import search_similar


def normalize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def lexical_overlap_score(query: str, text: str) -> float:
    q_tokens = set(normalize(query))
    t_tokens = set(normalize(text))

    if not q_tokens or not t_tokens:
        return 0.0

    overlap = q_tokens.intersection(t_tokens)
    return len(overlap) / len(q_tokens)


def rewrite_query_if_needed(query: str) -> str:
    q = query.strip().lower()

    personal_queries = {
        "tell about me",
        "tell me about me",
        "what do you know about me",
        "who am i",
        "describe me",
    }

    if q in personal_queries:
        return "user background goals preferences learning style skills recurring personal context"

    return query


def is_small_talk(query: str) -> bool:
    q = query.strip().lower()
    return q in {"hi", "hello", "hey", "yo", "hii", "hey there", "hello there"}


def retrieve_top_k(query: str, k: int = TOP_K) -> list[dict]:
    if is_small_talk(query):
        return []

    rewritten_query = rewrite_query_if_needed(query)
    query_vector = embed_query(rewritten_query)

    raw_results = search_similar(query_vector=query_vector, limit=RETRIEVE_K)

    deduped = []
    seen = set()
    for doc in raw_results:
        key = (
            doc["session_id"],
            doc["turn_start"],
            doc["turn_end"],
            doc["text"][:200]
        )
        if key not in seen:
            seen.add(key)
            deduped.append(doc)

    reranked = []
    for doc in deduped:
        lexical = lexical_overlap_score(query, doc["text"])
        hybrid_score = (0.75 * doc["score"]) + (0.25 * lexical)
        doc["lexical_score"] = lexical
        doc["hybrid_score"] = hybrid_score
        reranked.append(doc)

    reranked.sort(key=lambda d: d["hybrid_score"], reverse=True)
    return reranked[:k]