import sys
import os
import numpy as np

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.embeddings import EmbeddingPipeline

def test_embeddings():
    print("Testing embeddings generation...")
    
    pipeline = EmbeddingPipeline()
    
    mock_chunks = [
        {"chunk_id": "c1", "text": "This is a test chunk about machine learning.", "source": "test.pdf", "page": 1, "section": "s1"},
        {"chunk_id": "c2", "text": "Another test chunk regarding data pipelines.", "source": "test.pdf", "page": 1, "section": "s2"},
        {"chunk_id": "c3", "text": "Retrieval-augmented generation is cool.", "source": "test.pdf", "page": 2, "section": "s3"},
    ]
    
    embeddings, chunks = pipeline.embed_chunks(mock_chunks)
    
    # Assertions
    assert len(embeddings) == len(mock_chunks), f"Expected {len(mock_chunks)} embeddings, got {len(embeddings)}"
    assert len(chunks) == len(mock_chunks), "Chunk list length mismatch"
    assert chunks[0]["chunk_id"] == "c1", "Chunk ordering mismatch"
    
    # Verify dimensions (all-MiniLM-L6-v2 outputs 384 dimensions)
    assert embeddings.shape[1] == 384, f"Expected 384 dimensions, got {embeddings.shape[1]}"
    
    print("-" * 50)
    print(f"Number of chunks: {len(chunks)}")
    print(f"Embedding shape: {embeddings.shape}")
    print(f"Embedding dimension: {embeddings.shape[1]}")
    print("-" * 50)
    
    print("test_embeddings passed!")

if __name__ == "__main__":
    test_embeddings()
