from typing import Dict, Any
import pypdf

class PyPDFParserWrapper:
    """A wrapper around PyPDF that mimics LightningParse output format."""
    
    def __init__(self):
        pass
        
    def parse(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parses a PDF file using pypdf and returns the structured dictionary.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            A dictionary containing the parsed output ('pages', 'metadata', etc.)
        """
        reader = pypdf.PdfReader(pdf_path)
        
        metadata = reader.metadata or {}
        
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            
            # Treat each page as a single block
            pages.append({
                "page_num": i + 1,
                "blocks": [
                    {
                        "text": text,
                        "section_id": None
                    }
                ]
            })
            
        return {
            "metadata": dict(metadata),
            "pages": pages
        }

def parse_document_pypdf(pdf_path: str) -> Dict[str, Any]:
    """Helper function to parse a document using PyPDF directly."""
    parser = PyPDFParserWrapper()
    return parser.parse(pdf_path)
