import re
from config import USER_X_THRESHOLD


def clean_block_text(text: str) -> str:
    """
    Remove obvious export noise.
    """
    text = text.strip()

    noise_patterns = [
        r"^\d{2}/\d{2}/\d{4},\s*\d{2}:\d{2}",
        r"^https?://",
        r"^\d+/\d+$",
        r"^ChatGPT$",
        r"^Thought for \d+[smh].*$",
    ]

    for pattern in noise_patterns:
        if re.match(pattern, text, flags=re.I):
            return ""

    exact_noise = {
        "Presentation",
    }

    if text in exact_noise:
        return ""

    if text.lower().endswith(".pptx"):
        return ""

    if len(text) <= 1:
        return ""

    return text


def merge_consecutive_same_role(turns: list[dict]) -> list[dict]:
    """
    Merge consecutive blocks that belong to the same speaker.
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


def parse_turns_from_blocks(
    blocks: list[dict],
    user_x_threshold: float = USER_X_THRESHOLD
) -> list[dict]:
    """
    Infer User vs Assistant using horizontal position.
    """
    if not blocks:
        return []

    blocks = sorted(blocks, key=lambda b: (b["page"], b["y0"], b["x0"]))

    cleaned_blocks = []
    for block in blocks:
        cleaned_text = clean_block_text(block["text"])
        if not cleaned_text:
            continue

        cleaned_blocks.append({
            "page": block["page"],
            "x0": block["x0"],
            "y0": block["y0"],
            "text": cleaned_text,
        })

    turns = []
    for idx, block in enumerate(cleaned_blocks):
        role = "User" if block["x0"] >= user_x_threshold else "Assistant"
        turns.append({
            "turn_id": idx,
            "role": role,
            "content": block["text"],
        })

    return merge_consecutive_same_role(turns)