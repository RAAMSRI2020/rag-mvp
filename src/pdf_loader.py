import fitz  # PyMuPDF


def extract_pdf_blocks(pdf_path: str) -> list[dict]:
    """
    Extract text blocks with coordinates from a PDF.
    """
    doc = fitz.open(pdf_path)
    blocks_data = []

    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("blocks")
        for block in blocks:
            x0, y0, x1, y1, text, block_no, block_type = block
            cleaned = text.strip()
            if cleaned:
                blocks_data.append({
                    "page": page_num,
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                    "text": cleaned,
                })

    return blocks_data