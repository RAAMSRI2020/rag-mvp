def is_small_talk(query: str) -> bool:
    q = query.strip().lower()
    return q in {"hi", "hello", "hey", "yo", "hii", "hey there", "hello there"}


def is_profile_query(query: str) -> bool:
    q = query.strip().lower()

    strong_patterns = [
        "tell about me",
        "tell me about me",
        "what do you know about me",
        "who am i",
        "describe me",
        "summarize me",
        "say about me",
    ]

    if any(p in q for p in strong_patterns):
        return True

    has_me = " me" in f" {q} " or "about me" in q
    has_profile_intent = any(word in q for word in [
        "tell", "describe", "summarize", "say", "infer", "know"
    ])

    return has_me and has_profile_intent


def rewrite_query_if_needed(query: str) -> str:
    if is_profile_query(query):
        return "user background goals interests preferences learning style working style recurring concerns"
    return query


def analyze_query(query: str) -> str:
    if is_small_talk(query):
        return "small_talk"
    if is_profile_query(query):
        return "profile"
    return "general"
