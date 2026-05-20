import os
from typing import List, Dict

from config import WINDOW_SIZE, OVERLAP
from src.pdf_loader import extract_pdf_blocks
from src.parser import parse_turns_from_blocks
from src.chunker import build_snippets
from src.embedder import embed_texts
from src.vectordb import ensure_collection, upsert_snippets


def process_pdf_file(file_path: str, original_name: str) -> Dict:
    """
    Process a single PDF file end-to-end and return structured ingestion results.
    """
    session_id = os.path.splitext(original_name)[0]

    try:
        blocks = extract_pdf_blocks(file_path)
        turns = parse_turns_from_blocks(blocks)
        snippets = build_snippets(
            turns,
            window_size=WINDOW_SIZE,
            overlap=OVERLAP
        )

        if not snippets:
            return {
                "file_name": original_name,
                "session_id": session_id,
                "status": "failed",
                "reason": "No snippets created",
                "blocks_extracted": len(blocks),
                "turns_parsed": len(turns),
                "snippets_created": 0,
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
            "stored": False,
        }


def summarize_ingestion(results: List[Dict]) -> Dict:
    """
    Build a dashboard-style summary from per-file ingestion results.
    """
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