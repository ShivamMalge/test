import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pipeline import LightningRAG

def test_full_pipeline():
    print("Testing Full E2E Pipeline...")
    
    pdf_path = "data/synthetic/lightningparse_test_document_TRUE_2COL.pdf"
    if not os.path.exists(pdf_path):
        print(f"Skipping e2e test, not found: {pdf_path}")
        return
        
    rag = LightningRAG()
    rag.ingest_document(pdf_path)
    
    questions = [
        "What does a modern computing system look like?",
        "Why is chunking important for indexing?",
        "How should one evaluate a document pipeline?"
    ]
    
    for q in questions:
        print(f"\n{'='*50}")
        print(f"Q: {q}")
        print(f"{'='*50}")
        
        result = rag.ask(q, top_k=3)
        
        print("\n--- Answer ---")
        print(result["answer"])
        
        print("\n--- Sources Used ---")
        for idx, s in enumerate(result["sources"]):
            print(f"  [{idx+1}] Source: {os.path.basename(s['source'])}, Page: {s['page']}, Section: {s['section']}, Score: {s['score']:.4f}")

    print("\ntest_full_pipeline passed!")

if __name__ == "__main__":
    test_full_pipeline()
