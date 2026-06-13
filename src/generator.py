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



def extract_headings_and_topics(text: str) -> Dict[str, List[str]]:
    lines = split_lines(text)
    sections = {}
    current_heading = None

    for line in lines:
        heading_match = re.match(r"^(Block\s+\d+\s+—\s+.+)$", line)
        if heading_match:
            current_heading = heading_match.group(1)
            sections[current_heading] = []
            continue

        if current_heading and re.match(r"^\d+\.\s+", line):
            item = re.sub(r"^\d+\.\s+", "", line).strip()
            sections[current_heading].append(item)

    return sections


def answer_topic_list_query(docs: List[Dict]) -> str:
    combined = "\n".join(clean_text(doc["text"]) for doc in docs)
    sections = extract_headings_and_topics(combined)

    if sections:
        parts = ["The topics covered were:\n"]
        for heading, items in sections.items():
            parts.append(f"**{heading}**")
            for item in items:
                parts.append(f"- {item}")
            parts.append("")
        return "\n".join(parts).strip()

    return "I found relevant content, but I could not structure it cleanly into topic groups."



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

    q = query.strip().lower()

    if any(phrase in q for phrase in [
        "what are all the topics",
        "what topics",
        "topics covered",
        "covered during exam revision",
        "during exam revision",
    ]):
        return answer_topic_list_query(docs)

    return generate_general_answer(query, docs, quality)