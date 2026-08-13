import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.pipeline import LightningRAG

def evaluate():
    rag = LightningRAG()
    pdf_path = "data/books/VTU 7th Sem Study Strategy.pdf"
    rag.ingest_document(pdf_path)
    
    questions = [
        "What is the fundamental objective of BCS702?",
        "Why is the transition to the final year of an engineering curriculum considered a critical inflection point?",
        "In Module 1 of BCS702, what topics do students frequently find highly confusing?",
        "What are the fundamental concepts taught in Module 1 related to Flynn's Taxonomy?",
        "How does the document contrast the scoring potential of SIMD vs MIMD differences with memorizing crossbar switch routing paths?"
    ]
    
    for i, q in enumerate(questions):
        print(f"\n{'='*50}")
        print(f"[{i+1}] Q: {q}")
        print(f"{'='*50}")
        
        result = rag.ask(q, top_k=2)
        print("\n--- Generated Answer ---")
        print(result["answer"])
        print("\n--- Sources Used ---")
        for idx, s in enumerate(result["sources"]):
            print(f"  [{idx+1}] Source: {os.path.basename(s['source'])}, Page: {s['page']}, Section: {s['section']}, Score: {s['score']:.4f}")
            
        if i < len(questions) - 1:
            print("\nWaiting 10 seconds to avoid Gemini rate limits...")
            time.sleep(10)

if __name__ == "__main__":
    evaluate()
