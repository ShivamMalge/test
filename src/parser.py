import json
import lightningparse
from typing import Dict, Any

class ParserWrapper:
    """A thin wrapper around LightningParse."""
    
    def __init__(self):
        pass
        
    def parse(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parses a PDF file and returns the structured dictionary.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            A dictionary containing the parsed output ('pages', 'metadata', etc.)
        """
        raw_result = lightningparse.parse_pdf(pdf_path)
        # lightningparse returns a JSON string, so we parse it into a dict
        if isinstance(raw_result, str):
            return json.loads(raw_result)
        return raw_result

def parse_document(pdf_path: str) -> Dict[str, Any]:
    """Helper function to parse a document directly."""
    parser = ParserWrapper()
    return parser.parse(pdf_path)
