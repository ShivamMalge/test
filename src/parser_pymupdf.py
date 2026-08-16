from typing import Dict, Any, List
import fitz  # PyMuPDF


def _midpoint_inside(bbox, regions) -> bool:
    x0, y0, x1, y1 = bbox
    h_mid, v_mid = (x0 + x1) / 2, (y0 + y1) / 2
    return any(
        rx0 <= h_mid < rx1 and ry0 <= v_mid < ry1
        for rx0, ry0, rx1, ry1 in regions
    )


class PyMuPDFParserWrapper:
    """
    A wrapper around PyMuPDF (fitz) that mimics the LightningParse output format.

    PyMuPDF returns block-level text, so this is the closest structural analogue to
    LightningParse among the baselines. Tables are extracted through `find_tables`
    and their regions are excluded from the text blocks to avoid double counting.

    Note: PyMuPDF is AGPL-licensed, unlike the other parsers benchmarked here.
    """

    def __init__(self):
        pass

    def parse(self, pdf_path: str) -> Dict[str, Any]:
        pages: List[Dict[str, Any]] = []

        with fitz.open(pdf_path) as doc:
            metadata = dict(doc.metadata or {})

            for i, page in enumerate(doc):
                blocks: List[Dict[str, Any]] = []

                try:
                    tables = list(page.find_tables())
                except Exception:
                    tables = []
                table_regions = [t.bbox for t in tables]

                for x0, y0, x1, y1, text, _block_no, block_type in page.get_text("blocks"):
                    if block_type != 0 or not text.strip():
                        continue  # skip image blocks
                    if _midpoint_inside((x0, y0, x1, y1), table_regions):
                        continue  # covered by a table block below
                    blocks.append({"type": "text", "text": text, "section_id": None})

                for table in tables:
                    rows = [
                        [(cell or "").replace("\n", " ").strip() for cell in row]
                        for row in table.extract()
                    ]
                    rows = [row for row in rows if any(row)]
                    if rows:
                        blocks.append({"type": "table", "rows": rows, "section_id": None})

                pages.append({"page_num": i + 1, "blocks": blocks})

        return {"metadata": metadata, "pages": pages}


def parse_document_pymupdf(pdf_path: str) -> Dict[str, Any]:
    """Helper function to parse a document using PyMuPDF directly."""
    return PyMuPDFParserWrapper().parse(pdf_path)
