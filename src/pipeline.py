import os
import re
from typing import List, Dict

from config import WINDOW_SIZE, OVERLAP, MAX_UNIT_CHARS
from src.intent import analyze_query
from src.retriever import retrieve_top_k
from src.generator import generate_answer
from src.pdf_loader import extract_pdf_blocks
from src.parser import parse_turns_from_blocks
from src.chunker import build_snippets
from src.embedder import embed_texts
from src.vectordb import ensure_collection, upsert_snippets


def is_good_snippet(text: str) -> bool:
    """
    Reject noisy, symbolic, or ultra-short snippets.
    """
    text = text.strip()

    if len(text) < 80:
        return False

    weird_symbol_ratio = sum(
        1 for c in text if not c.isalnum() and c not in " \n.,:;!?'-()"
    ) / max(len(text), 1)
    if weird_symbol_ratio > 0.20:
        return False

    words = re.findall(r"[A-Za-z]{2,}", text)
    if len(words) < 15:
        return False

    junk_patterns = [
        r"𝒖:|𝒄:|FC",
        r"\bA'\b",
        r"\bco\b",
        r"^Presentation$",
        r"\.pptx",
    ]
    for pattern in junk_patterns:
        if re.search(pattern, text):
            return False

    return True


def process_pdf_file(file_path: str, original_name: str) -> Dict:
    session_id = os.path.splitext(original_name)[0]

    try:
        blocks = extract_pdf_blocks(file_path)
        turns = parse_turns_from_blocks(blocks)
        snippets = build_snippets(
            turns,
            window_size=WINDOW_SIZE,
            overlap=OVERLAP,
            max_chars=MAX_UNIT_CHARS,
        )

        raw_snippet_count = len(snippets)
        snippets = [s for s in snippets if is_good_snippet(s["text"])]

        if not snippets:
            return {
                "file_name": original_name,
                "session_id": session_id,
                "status": "failed",
                "reason": "No good snippets remained after filtering",
                "blocks_extracted": len(blocks),
                "turns_parsed": len(turns),
                "snippets_created": 0,
                "raw_snippets_created": raw_snippet_count,
                "stored": False,
            }

        texts = [snippet["text"] for snippet in snippets]
        embeddings = embed_texts(texts)

        ensure_collection()
        upsert_snippets(
            snippets=snippets,
            embeddings=embeddings,
            session_id=session_id,
            source_pdf=original_name
        )

        return {
            "file_name": original_name,
            "session_id": session_id,
            "status": "success",
            "reason": "",
            "blocks_extracted": len(blocks),
            "turns_parsed": len(turns),
            "snippets_created": len(snippets),
            "raw_snippets_created": raw_snippet_count,
            "stored": True,
        }

    except Exception as e:
        return {
            "file_name": original_name,
            "session_id": session_id,
            "status": "failed",
            "reason": str(e),
            "blocks_extracted": 0,
            "turns_parsed": 0,
            "snippets_created": 0,
            "raw_snippets_created": 0,
            "stored": False,
        }


def summarize_ingestion(results: List[Dict]) -> Dict:
    total_files = len(results)
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = total_files - success_count
    total_turns = sum(r["turns_parsed"] for r in results)
    total_snippets = sum(r["snippets_created"] for r in results)

    return {
        "total_files": total_files,
        "success_count": success_count,
        "failed_count": failed_count,
        "total_turns": total_turns,
        "total_snippets": total_snippets,
    }


def answer_query(query: str) -> dict:
    intent = analyze_query(query)
    docs = retrieve_top_k(query)
    answer = generate_answer(query, docs)
    return {"query": query, "intent": intent, "docs": docs, "answer": answer}