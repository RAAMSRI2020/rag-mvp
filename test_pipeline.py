import os

from config import PDF_DIR, WINDOW_SIZE, OVERLAP
from src.pdf_loader import extract_pdf_blocks
from src.parser import parse_turns_from_blocks
from src.chunker import build_snippets


def main():
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print("No PDFs found in data/pdfs")
        return

    first_pdf = os.path.join(PDF_DIR, pdf_files[0])
    print(f"Reading: {first_pdf}\n")

    blocks = extract_pdf_blocks(first_pdf)

    print("=== FIRST 15 BLOCKS ===")
    for block in blocks[:15]:
        print({
            "page": block["page"],
            "x0": round(block["x0"], 2),
            "y0": round(block["y0"], 2),
            "text": block["text"][:120]
        })
        print()

    turns = parse_turns_from_blocks(blocks)
    print(f"\nTotal turns parsed: {len(turns)}")

    if turns:
        print("\n=== FIRST 6 TURNS ===")
        for turn in turns[:6]:
            print(turn)
            print()

    snippets = build_snippets(turns, window_size=WINDOW_SIZE, overlap=OVERLAP)
    print(f"Total snippets created: {len(snippets)}")

    if snippets:
        print("\n=== FIRST 2 SNIPPETS ===")
        for snippet in snippets[:2]:
            print(snippet)
            print()


if __name__ == "__main__":
    main()