def build_snippets(turns: list[dict], window_size: int = 4, overlap: int = 2) -> list[dict]:
    """
    Build sliding-window snippets from conversation turns.

    Example:
    turns 0-3
    then 2-5
    then 4-7
    """
    snippets = []

    if not turns:
        return snippets

    step = max(1, window_size - overlap)

    for start in range(0, len(turns), step):
        window = turns[start:start + window_size]

        if not window:
            continue

        snippet_text = "\n".join(
            f"{turn['role']}: {turn['content']}" for turn in window
        )

        snippets.append({
            "turn_start": window[0]["turn_id"],
            "turn_end": window[-1]["turn_id"],
            "text": snippet_text
        })

        if start + window_size >= len(turns):
            break

    return snippets