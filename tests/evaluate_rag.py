import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.pipeline import LightningRAG

import time

def evaluate():
    rag = LightningRAG()
    pdf_path = "data/synthetic/lightningparse_test_document_TRUE_2COL.pdf"
    rag.ingest_document(pdf_path)
    
    questions = [
        "Which stage of the pipeline can lose evidence before the embedding model ever sees it?",
        "Why do boundaries matter in a layered design according to the document?",
        "Why is semantic similarity not the same thing as factual correctness?",
        "According to the test table, which system achieved the highest recall and what was its value?",
        "How does the document suggest keyword retrieval and semantic retrieval interact?"
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
