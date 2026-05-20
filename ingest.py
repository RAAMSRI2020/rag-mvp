import os

from config import PDF_DIR, WINDOW_SIZE, OVERLAP
from src.pdf_loader import extract_pdf_blocks
from src.parser import parse_turns_from_blocks
from src.chunker import build_snippets
from src.embedder import embed_texts
from src.vectordb import ensure_collection, upsert_snippets, close_client


def ingest_all_pdfs():
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print("No PDFs found in data/pdfs")
        return

    print("Starting ingestion...")
    ensure_collection()

    for pdf_file in pdf_files:
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        session_id = os.path.splitext(pdf_file)[0]

        print(f"Processing: {pdf_file}")

        blocks = extract_pdf_blocks(pdf_path)
        turns = parse_turns_from_blocks(blocks)
        snippets = build_snippets(
            turns,
            window_size=WINDOW_SIZE,
            overlap=OVERLAP
        )

        print(f"Parsed turns: {len(turns)} | Snippets: {len(snippets)}")

        if not snippets:
            print(f"Skipped {pdf_file}: no snippets created")
            continue

        texts = [snippet["text"] for snippet in snippets]
        embeddings = embed_texts(texts)

        upsert_snippets(
            snippets=snippets,
            embeddings=embeddings,
            session_id=session_id,
            source_pdf=pdf_file
        )

        print(f"Inserted {len(snippets)} snippets from {pdf_file}")

    print("Ingestion complete.")


if __name__ == "__main__":
    try:
        ingest_all_pdfs()
    finally:
        close_client()