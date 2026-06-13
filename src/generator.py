from typing import List, Dict
import re
from src.intent import is_small_talk


def clean_text(text: str) -> str:
    text = text.replace("User:", "").replace("Assistant:", "").strip()
    text = re.sub(r"\n{2,}", "\n", text)
    return text


def split_lines(text: str):
    return [line.strip(" -•\t") for line in text.splitlines() if line.strip()]



def classify_result_quality(docs: List[Dict]) -> str:
    if not docs:
        return "none"

    best_score = docs[0].get("hybrid_score", docs[0]["score"])
    if best_score >= 0.45:
        return "strong"
    elif best_score >= 0.30:
        return "usable"
    return "weak"





def generate_general_answer(query: str, docs: List[Dict], quality: str) -> str:
    top_doc = docs[0]
    cleaned = clean_text(top_doc["text"])
    lines = split_lines(cleaned)

    short_lines = []
    for line in lines:
        if len(short_lines) >= 8:
            break
        if len(line) > 10:
            short_lines.append(line)

    summary = "\n".join(short_lines[:8]).strip()

    if quality == "usable":
        return (
            "I found relevant context in the indexed sessions:\n\n"
            f"{summary}\n\n"
            f"This answer is mainly based on session '{top_doc['session_id']}'. "
            "You can review the supporting evidence below."
        )

    return (
        "Based on the indexed sessions, the most relevant context is:\n\n"
        f"{summary}\n\n"
        f"This answer is based primarily on session '{top_doc['session_id']}'. "
        "See the supporting evidence below for the retrieved snippets."
    )


def generate_answer(query: str, docs: List[Dict]) -> str:
    if is_small_talk(query):
        return "Hi. Ask me something about the indexed sessions, and I’ll answer using the uploaded conversation history."

    if not docs:
        return "I could not find relevant information in the indexed sessions."

    quality = classify_result_quality(docs)

    if quality == "weak":
        return (
            "I found indexed content, but the matches are too weak to answer reliably. "
            "Try a more specific question, or upload cleaner conversation-session PDFs."
        )

    return generate_general_answer(query, docs, quality)