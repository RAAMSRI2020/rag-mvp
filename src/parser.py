import re


def clean_block_text(text: str) -> str:
    """
    Remove obvious export noise from browser-exported chat PDFs.
    """
    text = text.strip()

    noise_patterns = [
        r"^\d{2}/\d{2}/\d{4},\s*\d{2}:\d{2}",   # timestamp
        r"^https?://",                          # URLs
        r"^\d+/\d+$",                           # page count like 1/25
        r"^ChatGPT$",                           # heading
        r"^Thought for \d+[smh].*$",            # Thought for 15s / 2m 2s
        r"^Data Visualisation and Tableau$",    # title line in your sample
    ]

    for pattern in noise_patterns:
        if re.match(pattern, text, flags=re.I):
            return ""

    # exact noise blocks from uploaded-file/export artifacts
    exact_noise = {
        "Presentation",
    }
    if text in exact_noise:
        return ""

    # file attachment lines or upload artifacts
    if text.lower().endswith(".pptx"):
        return ""

    # very short junk
    if len(text) <= 1:
        return ""

    return text


def merge_consecutive_same_role(turns: list[dict]) -> list[dict]:
    """
    Merge consecutive blocks that belong to the same role.
    One message may be split into many blocks in the PDF.
    """
    if not turns:
        return []

    merged = [turns[0].copy()]

    for turn in turns[1:]:
        if turn["role"] == merged[-1]["role"]:
            merged[-1]["content"] += "\n" + turn["content"]
        else:
            merged.append(turn.copy())

    for idx, turn in enumerate(merged):
        turn["turn_id"] = idx

    return merged


def parse_turns_from_blocks(blocks: list[dict], user_x_threshold: float = 150.0) -> list[dict]:
    """
    Parse conversation turns from positioned PDF blocks.

    Heuristic:
    - blocks on the right / more indented => User
    - blocks on the left => Assistant
    """
    cleaned_blocks = []

    # safer ordering
    blocks = sorted(blocks, key=lambda b: (b["page"], b["y0"], b["x0"]))

    for block in blocks:
        cleaned_text = clean_block_text(block["text"])
        if not cleaned_text:
            continue

        cleaned_blocks.append({
            "page": block["page"],
            "x0": block["x0"],
            "y0": block["y0"],
            "text": cleaned_text
        })

    turns = []
    for idx, block in enumerate(cleaned_blocks):
        role = "User" if block["x0"] >= user_x_threshold else "Assistant"

        turns.append({
            "turn_id": idx,
            "role": role,
            "content": block["text"]
        })

    return merge_consecutive_same_role(turns)