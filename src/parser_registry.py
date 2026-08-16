"""
Single source of truth for the parsers the pipeline and benchmark can use.

Every entry maps a parser name to a callable with the same contract:
    parse(pdf_path) -> {"metadata": {...}, "pages": [{"page_num": int, "blocks": [...]}]}

Blocks are either {"type": "text", "text": str, "section_id": ...} or
{"type": "table", "rows": [[str, ...], ...], "section_id": ...}.

Because the benchmark times these exact callables, the measured latency is the
code path the pipeline actually pays for, identically for every parser.
"""

from typing import Callable, Dict, Any

from src.parser import parse_document
from src.parser_pypdf import parse_document_pypdf
from src.parser_pdfplumber import parse_document_pdfplumber
from src.parser_pymupdf import parse_document_pymupdf

ParseFn = Callable[[str], Dict[str, Any]]

PARSERS: Dict[str, ParseFn] = {
    "lightningparse": parse_document,
    "pypdf": parse_document_pypdf,
    "pdfplumber": parse_document_pdfplumber,
    "pymupdf": parse_document_pymupdf,
}


def get_parser(parser_type: str) -> ParseFn:
    try:
        return PARSERS[parser_type]
    except KeyError:
        raise ValueError(
            f"Unknown parser_type {parser_type!r}. Available: {sorted(PARSERS)}"
        ) from None
