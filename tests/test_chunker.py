import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parser import parse_document
from src.chunker import Chunker, print_chunks

def test_chunker_basic():
    # Mock document to test logic
    mock_doc = {
        "pages": [
            {
                "page_num": 1,
                "blocks": [
                    {"type": "text", "text": "Short block.", "section_id": "sec1"},
                    {"type": "text", "text": " Another short block.", "section_id": "sec1"},
                    {"type": "text", "text": "   ", "section_id": "sec1"}, # Empty block
                    {"type": "text", "text": "New section.", "section_id": "sec2"}
                ]
            },
            {
                "page_num": 2,
                "blocks": [
                    {"type": "text", "text": "A " * 1000, "section_id": "sec3"} # Large block
                ]
            }
        ]
    }
    
    chunker = Chunker(max_chunk_size=1500, min_chunk_size=10)
    chunks = chunker.chunk_document(mock_doc, "mock.pdf")
    
    # Assertions
    # Page 1, Sec 1 (combined) -> 1 chunk
    # Page 1, Sec 2 (too short, but it's end of page so it gets appended if >= min_chunk_size. "New section." is 12 chars) -> 1 chunk
    # Page 2, Sec 3 (split) -> 2 chunks
    
    assert len(chunks) == 4, f"Expected 4 chunks, got {len(chunks)}"
    assert chunks[0]["section"] == "sec1"
    assert chunks[0]["page"] == 1
    assert "Short block.\n\nAnother short block." in chunks[0]["text"]
    
    assert chunks[1]["section"] == "sec2"
    
    assert chunks[2]["page"] == 2
    assert chunks[2]["section"] == "sec3"
    assert len(chunks[2]["text"]) <= 1500
    
    assert chunks[3]["page"] == 2
    assert chunks[3]["section"] == "sec3"
    
    print("test_chunker_basic passed!")

def test_chunker_real_document():
    pdf_path = "data/synthetic/lightningparse_test_document_TRUE_2COL.pdf"
    if not os.path.exists(pdf_path):
        print(f"Skipping real doc test, not found: {pdf_path}")
        return
        
    print(f"\nParsing and chunking {pdf_path}...")
    parsed_doc = parse_document(pdf_path)
    
    chunker = Chunker(max_chunk_size=1000)
    chunks = chunker.chunk_document(parsed_doc, pdf_path)
    
    assert len(chunks) > 0
    # Check that chunks retain metadata
    for chunk in chunks:
        assert "text" in chunk
        assert "source" in chunk
        assert "page" in chunk
        assert "section" in chunk
        assert "chunk_id" in chunk
        assert len(chunk["text"]) >= chunker.min_chunk_size
        
    print_chunks(chunks[:10]) # Print first 10 for inspection
    print(f"\ntest_chunker_real_document passed! Total chunks: {len(chunks)}")

if __name__ == "__main__":
    test_chunker_basic()
    test_chunker_real_document()
