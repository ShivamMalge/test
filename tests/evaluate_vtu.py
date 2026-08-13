import sys
import os
import time
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.pipeline import LightningRAG

def evaluate():
    rag = LightningRAG()
    pdf_path = "data/books/VTU 7th Sem Study Strategy.pdf"
    
    print(f"Ingesting {pdf_path}...")
    rag.ingest_document(pdf_path)
    
    print(f"Index size: {rag.retriever.index.ntotal if rag.retriever.index else 0} chunks")
    
    questions = [
        "What is the overall study strategy recommended?",
        "How should one prepare for the internal exams?",
        "What resources are suggested for studying?",
        "How is the syllabus divided?",
        "What is the advice regarding previous year question papers?"
    ]
    
    for i, q in enumerate(questions):
        print(f"\n{'='*50}")
        print(f"question_id: vtu_{i+1}")
        print(f"question: {q}")
        
        result = rag.ask(q, top_k=2)
        
        print("expected_answer: (N/A for new PDF)")
        print("expected_page: (N/A)")
        print("expected_section: (N/A)")
        
        chunks_info = []
        for s in result["sources"]:
            chunks_info.append(f"Page {s['page']} Section {s['section']} (Score: {s['score']:.4f})")
        print(f"retrieved_chunks: {', '.join(chunks_info)}")
        
        print(f"generated_answer: {result['answer'].strip()}")
        print("answer_correct: ")
        print("citation_correct: ")
        print("notes: ")
        
        if i < len(questions) - 1:
            print("\nWaiting 10 seconds to avoid Gemini rate limits...")
            time.sleep(10)

if __name__ == "__main__":
    evaluate()
