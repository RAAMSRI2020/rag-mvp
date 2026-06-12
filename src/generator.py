from typing import List, Dict
import re
from src.intent import is_small_talk, is_profile_query


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


def generate_profile_answer(docs: List[Dict]) -> str:
    session_names = sorted({doc["session_id"] for doc in docs})
    combined = "\n".join(clean_text(doc["text"]) for doc in docs).lower()

    observations = []

    if any(x in combined for x in [
        "exam", "revision", "lecture", "pca", "svm", "machine learning",
        "zustand", "react", "hpc", "mapreduce", "spark", "cloud"
    ]):
        observations.append(
            "You seem to be working across technical and academic topics, especially computing, software, and exam-related study material."
        )

    if any(x in combined for x in [
        "shortcut", "formula", "memorise", "memory", "template", "step", "base formula", "modifier"
    ]):
        observations.append(
            "You prefer practical learning methods such as shortcuts, formulas, templates, and step-by-step guidance."
        )

    if any(x in combined for x in [
        "exam", "asap", "need", "must", "target", "plan"
    ]):
        observations.append(
            "Your questions are usually goal-driven, meaning you ask for help to solve something quickly, prepare effectively, or improve performance."
        )

    if any(x in combined for x in [
        "burger", "gmail", "react", "machine learning", "cloud", "mapreduce"
    ]):
        observations.append(
            "You work across both academic/technical topics and practical real-world tasks, rather than focusing on only one domain."
        )

    if any(x in combined for x in [
        "shortcut", "must remember", "revision", "summary", "key things", "fastest way"
    ]):
        observations.append(
            "You seem to value concise, usable help more than long theoretical explanations."
        )

    if not observations:
        observations.append(
            "The indexed sessions suggest some recurring interests and tasks, but the current evidence is not strong enough to form a detailed profile."
        )

    bullets = "\n".join(f"- {item}" for item in observations[:5])
    sessions = ", ".join(session_names[:6])

    return (
        "From the indexed sessions, here is what I can reasonably infer about you:\n\n"
        f"{bullets}\n\n"
        f"These observations are based on patterns retrieved across these sessions: {sessions}."
    )


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


def answer_burger_query(docs: List[Dict]) -> str:
    combined = "\n".join(clean_text(doc["text"]) for doc in docs).lower()

    parts = ["From the indexed burger session, you mainly dealt with:\n"]

    if any(x in combined for x in ["hamburger", "cheeseburger", "double cheeseburger"]):
        parts.append("**1. Hamburger family**")
        parts.append("- Hamburger")
        parts.append("- Cheeseburger")
        parts.append("- Double Cheeseburger")
        parts.append("- Base formula: mustard + ketchup + pickles + patty")
        parts.append("")

    if "whopper" in combined:
        parts.append("**2. Whopper family**")
        parts.append("- Whopper-style layered build")
        parts.append("- mayo, lettuce, tomato, onion, ketchup, pickles, patty")
        parts.append("")

    if any(x in combined for x in ["bbq", "xl", "stacker", "onion rings", "bacon"]):
        parts.append("**3. BBQ / XL / Stacker family**")
        parts.append("- BBQ-heavy builds")
        parts.append("- onion rings, bacon, cheese, double patties")
        parts.append("")

    if any(x in combined for x in ["sauce position", "veg position", "cheese rule", "bacon rule", "onion rule", "patty identification"]):
        parts.append("**4. Build rules you were taught**")
        parts.append("- sauce position rule")
        parts.append("- veg position rule")
        parts.append("- cheese rule")
        parts.append("- bacon rule")
        parts.append("- onion rule")
        parts.append("- patty identification")
        parts.append("")

    if any(x in combined for x in ["rush hour", "memorise", "priority burgers", "build order shortcut", "modifiers"]):
        parts.append("**5. Speed and memorisation method**")
        parts.append("- think in burger families, not individual burgers")
        parts.append("- use base build + modifiers")
        parts.append("- identify burger family first, then add extras")
        parts.append("")

    return "\n".join(parts).strip()


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

    if is_profile_query(query):
        return generate_profile_answer(docs)

    if any(phrase in q for phrase in [
        "what are all the topics",
        "what topics",
        "topics covered",
        "covered during exam revision",
        "during exam revision",
    ]):
        return answer_topic_list_query(docs)

    if any(word in q for word in ["burger", "burgers", "sandwich", "dealt with"]):
        return answer_burger_query(docs)

    return generate_general_answer(query, docs, quality)