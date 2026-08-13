import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parser import parse_document

def inspect_parser_output(pdf_path: str):
    print(f"Inspecting: {pdf_path}")
    print("-" * 50)
    
    result = parse_document(pdf_path)
    
    pages = result.get("pages", [])
    print(f"Number of pages: {len(pages)}")
    
    for page in pages:
        page_num = page.get("page_num")
        blocks = page.get("blocks", [])
        print(f"\n--- Page {page_num} ---")
        print(f"Number of blocks: {len(blocks)}")
        
        tables = [b for b in blocks if b.get("type") == "table"]
        if tables:
            print(f"Tables found: {len(tables)}")
        
        # Print first few blocks to see the reading order and structure
        print("First 5 blocks on this page:")
        for idx, block in enumerate(blocks[:5]):
            b_type = block.get("type")
            b_sec = block.get("section_id")
            b_text = block.get("text", "").replace("\n", " ")[:60]
            print(f"  Block {idx}: [{b_type}] (section: {b_sec}) -> {b_text}...")

if __name__ == "__main__":
    pdf_file = "data/synthetic/lightningparse_test_document_TRUE_2COL.pdf"
    if os.path.exists(pdf_file):
        inspect_parser_output(pdf_file)
    else:
        print(f"File not found: {pdf_file}")
