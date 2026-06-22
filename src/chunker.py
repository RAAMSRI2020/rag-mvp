def _split_turn_into_units(turn: dict, max_chars: int) -> list[dict]:
    role = turn["role"]
    content = turn["content"] or ""

    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    if not paragraphs:
        stripped = content.strip()
        if stripped:
            paragraphs = [stripped]
        else:
            return []

    pieces: list[str] = []
    for para in paragraphs:
        if len(para) <= max_chars:
            pieces.append(para)
        else:
            for i in range(0, len(para), max_chars):
                chunk = para[i : i + max_chars].strip()
                if chunk:
                    pieces.append(chunk)

    return [{"role": role, "content": piece} for piece in pieces]


def build_snippets(
    turns: list[dict],
    window_size: int = 4,
    overlap: int = 2,
    max_chars: int = 500,
) -> list[dict]:
    """
    Build overlapping snippets from conversation turns.
    Each turn is first split into paragraph-sized units (further capped at
    max_chars) so a single very long turn produces multiple indexable units.
    """
    if not turns:
        return []

    units: list[dict] = []
    for turn in turns:
        for unit in _split_turn_into_units(turn, max_chars):
            units.append({**unit, "turn_id": len(units)})

    if not units:
        return []

    snippets = []
    step = max(1, window_size - overlap)

    for start in range(0, len(units), step):
        window = units[start : start + window_size]
        if not window:
            continue

        snippet_text = "\n".join(
            f"{unit['role']}: {unit['content']}" for unit in window
        )

        snippets.append({
            "turn_start": window[0]["turn_id"],
            "turn_end": window[-1]["turn_id"],
            "text": snippet_text,
        })

        if start + window_size >= len(units):
            break

    return snippets