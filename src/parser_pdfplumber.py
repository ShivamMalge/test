from typing import Dict, Any, List
import pdfplumber


def _not_within_bboxes(obj, bboxes) -> bool:
    """True when a pdfplumber object's midpoint falls outside every given bbox."""
    h_mid = (obj["x0"] + obj["x1"]) / 2
    v_mid = (obj["top"] + obj["bottom"]) / 2
    return not any(
        x0 <= h_mid < x1 and top <= v_mid < bottom
        for x0, top, x1, bottom in bboxes
    )


class PDFPlumberParserWrapper:
    """
    A wrapper around pdfplumber that mimics the LightningParse output format.

    pdfplumber has a real table API, so tables are emitted as `rows` blocks in the
    same shape LightningParse uses, and the table regions are filtered out of the
    text pass so their content is not counted twice.
    """

    def __init__(self):
        pass

    def parse(self, pdf_path: str) -> Dict[str, Any]:
        pages: List[Dict[str, Any]] = []

        with pdfplumber.open(pdf_path) as pdf:
            metadata = dict(pdf.metadata or {})

            for i, page in enumerate(pdf.pages):
                blocks: List[Dict[str, Any]] = []

                tables = page.find_tables()
                table_bboxes = [t.bbox for t in tables]

                # Text, with the table regions removed.
                if table_bboxes:
                    text_page = page.filter(lambda obj: _not_within_bboxes(obj, table_bboxes))
                else:
                    text_page = page
                text = text_page.extract_text() or ""

                if text.strip():
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


def parse_document_pdfplumber(pdf_path: str) -> Dict[str, Any]:
    """Helper function to parse a document using pdfplumber directly."""
    return PDFPlumberParserWrapper().parse(pdf_path)
