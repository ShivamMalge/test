import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.pipeline import LightningRAG

def evaluate():
    rag = LightningRAG()
    pdf_path = "data/books/_OceanofPDF.com_The_Prince_-_Niccolo_Machiavelli.pdf"
    
    print(f"Ingesting {pdf_path}...")
    rag.ingest_document(pdf_path)
    
    print(f"Index size: {rag.retriever.index.ntotal} chunks")
    
    questions = [
        "According to Chapter 1, what are the two kinds of principalities?",
        "What is Machiavelli's view on mercenaries?",
        "Why is it better for a prince to be feared than loved, according to the text?",
        "What examples from history does Machiavelli use to explain armed prophets?",
        "How should a prince handle flatterers?"
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
