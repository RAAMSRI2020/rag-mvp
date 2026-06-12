import re
from config import TOP_K, RETRIEVE_K
from src.embedder import embed_query
from src.vectordb import search_similar
from src.intent import is_small_talk, is_profile_query, rewrite_query_if_needed


def normalize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def lexical_overlap_score(query: str, text: str) -> float:
    q_tokens = set(normalize(query))
    t_tokens = set(normalize(text))
    if not q_tokens or not t_tokens:
        return 0.0
    return len(q_tokens.intersection(t_tokens)) / len(q_tokens)



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

    if is_profile_query(query):
        diversified = []
        used_sessions = set()

        for doc in reranked:
            if doc["session_id"] not in used_sessions:
                diversified.append(doc)
                used_sessions.add(doc["session_id"])
            if len(diversified) >= 5:
                break

        for doc in reranked:
            if doc not in diversified:
                diversified.append(doc)
            if len(diversified) >= 6:
                break

        return diversified

    return reranked[:k]