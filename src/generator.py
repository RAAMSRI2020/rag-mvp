from typing import List, Dict
import re


def build_context(docs: List[Dict]) -> str:
    return "\n\n".join(
        f"[Session: {doc['session_id']} | Turns: {doc['turn_start']}-{doc['turn_end']}]\n{doc['text']}"
        for doc in docs
    )


def is_personal_query(query: str) -> bool:
    q = query.strip().lower()
    triggers = [
        "tell about me",
        "tell me about me",
        "what do you know about me",
        "who am i",
        "describe me",
    ]
    return any(t in q for t in triggers)


def is_small_talk(query: str) -> bool:
    q = query.strip().lower()
    return q in {"hi", "hello", "hey", "yo", "hii", "hey there", "hello there"}


def classify_result_quality(docs: List[Dict]) -> str:
    if not docs:
        return "none"

    best_score = docs[0].get("hybrid_score", docs[0]["score"])

    if best_score >= 0.45:
        return "strong"
    elif best_score >= 0.30:
        return "usable"
    else:
        return "weak"


def clean_text(text: str) -> str:
    text = text.replace("User:", "").replace("Assistant:", "").strip()
    text = re.sub(r"\n{2,}", "\n", text)
    return text


def split_lines(text: str) -> List[str]:
    return [line.strip(" -•\t") for line in text.splitlines() if line.strip()]


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


def answer_personal_query(docs: List[Dict]) -> str:
    session_names = ", ".join(sorted({doc["session_id"] for doc in docs}))
    bullets = []

    for doc in docs:
        cleaned = clean_text(doc["text"])
        bullets.append(f"- From **{doc['session_id']}**: {cleaned[:280]}...")

    return (
        "From the indexed sessions, I can infer a few things based on the retrieved context:\n\n"
        + "\n".join(bullets[:3])
        + f"\n\nThese observations are based on context retrieved from: {session_names}."
    )


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


def answer_general_query(query: str, docs: List[Dict], quality: str) -> str:
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

    if is_personal_query(query):
        return answer_personal_query(docs)

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

    return answer_general_query(query, docs, quality)