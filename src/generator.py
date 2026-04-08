def build_answer(query: str, docs: list[dict]) -> str:
    """
    MVP answer builder.
    For now, it answers using the retrieved snippets directly.
    """
    if not docs:
        return "No relevant conversation snippets were found."

    context = "\n\n".join(
        f"[Session: {doc['session_id']} | Turns: {doc['turn_start']}-{doc['turn_end']}]\n{doc['text']}"
        for doc in docs
    )

    return (
        f"User query: {query}\n\n"
        f"Top retrieved conversation snippets:\n\n{context}\n\n"
        "This MVP answer is grounded directly in the retrieved snippets."
    )