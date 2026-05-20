from typing import List, Dict


def build_context(docs: List[Dict]) -> str:
    """
    Convert retrieved snippets into a single context block.
    """
    return "\n\n".join(
        f"[Session: {doc['session_id']} | Turns: {doc['turn_start']}-{doc['turn_end']}]\n{doc['text']}"
        for doc in docs
    )


def build_prompt(query: str, docs: List[Dict]) -> str:
    """
    Build a grounding prompt for an LLM.
    """
    context = build_context(docs)

    return f"""
You are a helpful assistant answering a user's question using retrieved conversation history.

User question:
{query}

Retrieved context:
{context}

Instructions:
- Answer the question clearly and directly.
- Use the retrieved context as the main evidence.
- Do not simply copy the raw snippets unless necessary.
- If the context is not sufficient, say that clearly.
- Do not invent details that are not supported by the retrieved context.
"""


def generate_answer_fallback(query: str, docs: List[Dict]) -> str:
    """
    Fallback answer generator when no real LLM is connected yet.
    This is still better than dumping raw snippets as the main answer.
    """
    if not docs:
        return "I could not find relevant information in the indexed sessions."

    # Take strongest snippet as base
    top_doc = docs[0]
    context_preview = top_doc["text"][:1200].strip()

    return (
        f"Based on the indexed sessions, the most relevant context suggests:\n\n"
        f"{context_preview}\n\n"
        f"This answer is based primarily on session '{top_doc['session_id']}'. "
        f"See the retrieved evidence below for the full supporting snippets."
    )


def generate_answer(query: str, docs: List[Dict]) -> str:
    """
    Main answer function.

    Right now it uses fallback mode.
    Later, replace this with a real LLM call using build_prompt(query, docs).
    """
    return generate_answer_fallback(query, docs)