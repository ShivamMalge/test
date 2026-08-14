import json
from src.pipeline import LightningRAG

def debug():
    rag = LightningRAG()
    pdf_path = "data/books/VTU 7th Sem Study Strategy.pdf"
    rag.ingest_document(pdf_path)
    
    questions = [
        "What is the overall study strategy recommended?",
        "How should one prepare for the internal exams?",
        "What resources are suggested for studying?",
        "How is the syllabus divided?",
        "What is the advice regarding previous year question papers?"
    ]
    
    for q in questions:
        print(f"\n--- QUERY: {q} ---")
        # Reproduce retrieval step manually
        retriever = rag.retriever
        
        # FAISS
        query_embeddings, _ = retriever.embedding_pipeline.embed_chunks([{"text": q}])
        distances, indices = retriever.index.search(query_embeddings, 9)
        print("FAISS Top 3 Indices:", indices[0][:3])
        print("FAISS Top 3 Distances:", distances[0][:3])
        
        # BM25
        tokenized_query = q.lower().split()
        bm25_scores = retriever.bm25.get_scores(tokenized_query)
        bm25_indices = bm25_scores.argsort()[::-1][:9]
        print("BM25 Top 3 Indices:", bm25_indices[:3])
        print("BM25 Top 3 Scores:", bm25_scores[bm25_indices][:3])
        
if __name__ == "__main__":
    debug()
