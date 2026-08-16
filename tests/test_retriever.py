import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parser import parse_document
from src.chunker import Chunker
from src.embeddings import EmbeddingPipeline
from src.retriever import Retriever

def test_retriever_basic():
    print("Testing basic retrieval logic...")
    pipeline = EmbeddingPipeline()
    retriever = Retriever(pipeline)
    
    mock_chunks = [
        {"chunk_id": "c1", "text": "The capital of France is Paris.", "source": "geo.pdf", "page": 1, "section": "s1"},
        {"chunk_id": "c2", "text": "Machine learning uses neural networks.", "source": "ml.pdf", "page": 1, "section": "s2"},
        {"chunk_id": "c3", "text": "Python is a popular programming language.", "source": "code.pdf", "page": 2, "section": "s3"},
    ]
    
    embeddings, chunks = pipeline.embed_chunks(mock_chunks)
    
    # Test index builds
    retriever.build_index(embeddings, chunks)
    assert retriever.index is not None
    assert retriever.index.ntotal == 3
    
    # Test search & metadata
    results = retriever.search("What is the capital of France?", top_k=2)
    assert len(results) == 2 # k is respected
    
    top_result = results[0]
    assert "score" in top_result
    assert "text" in top_result
    assert "source" in top_result
    assert top_result["source"] == "geo.pdf" # Source metadata preserved
    assert top_result["page"] == 1
    
    # The lowest distance (score) should be the first one
    assert top_result["text"] == "The capital of France is Paris."
    
    print("test_retriever_basic passed!")


def test_retriever_incremental():
    """A second ingest must extend the index, not evict the first document."""
    pipeline = EmbeddingPipeline()
    retriever = Retriever(pipeline)

    doc_a = [{"chunk_id": "a1", "text": "The capital of France is Paris.", "source": "geo.pdf", "page": 1, "section": "s1"}]
    doc_b = [{"chunk_id": "b1", "text": "Machine learning uses neural networks.", "source": "ml.pdf", "page": 1, "section": "s2"}]

    for doc in (doc_a, doc_b):
        embeddings, chunks = pipeline.embed_chunks(doc)
        retriever.add_documents(embeddings, chunks)

    assert retriever.index.ntotal == 2, f"Expected 2 vectors, got {retriever.index.ntotal}"
    assert {c["source"] for c in retriever.chunks} == {"geo.pdf", "ml.pdf"}

    # Both documents remain reachable after the second ingest.
    assert retriever.search("What is the capital of France?", top_k=1)[0]["source"] == "geo.pdf"
    assert retriever.search("neural networks", top_k=1)[0]["source"] == "ml.pdf"

    print("test_retriever_incremental passed!")

def test_retriever_real_document():
    pdf_path = "data/synthetic/lightningparse_test_document_TRUE_2COL.pdf"
    if not os.path.exists(pdf_path):
        print(f"Skipping real doc test, not found: {pdf_path}")
        return
        
    print(f"\nBuilding retrieval index for {pdf_path}...")
    parsed_doc = parse_document(pdf_path)
    
    chunker = Chunker(max_chunk_size=1000)
    chunks = chunker.chunk_document(parsed_doc, pdf_path)
    
    pipeline = EmbeddingPipeline()
    embeddings, chunks = pipeline.embed_chunks(chunks)
    
    retriever = Retriever(pipeline)
    retriever.build_index(embeddings, chunks)
    
    queries = [
        "What does a modern computing system look like?",
        "Why is chunking important for indexing?",
        "How should one evaluate a document pipeline?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        results = retriever.search(query, top_k=3)
        for i, res in enumerate(results):
            preview = res["text"].replace("\n", " ")[:80]
            print(f"  [{i+1}] Score: {res['score']:.4f} | Page: {res['page']} | {preview}...")
            
    print("\ntest_retriever_real_document passed!")

if __name__ == "__main__":
    test_retriever_basic()
    test_retriever_incremental()
    test_retriever_real_document()
