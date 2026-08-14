import os
from typing import List, Dict, Any, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer

class EmbeddingPipeline:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initializes the embedding pipeline using local sentence-transformers.
        """
        self.model_name = model_name
        print(f"Loading local embedding model {model_name}...")
        self.model = SentenceTransformer(model_name)

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Embeds a list of chunks.
        
        Args:
            chunks: A list of chunk dictionaries.
            
        Returns:
            A tuple of (embeddings, chunks) where embeddings is a numpy array
            of shape (num_chunks, embedding_dim), and chunks is the list of 
            the original chunks.
        """
        if not chunks:
            return np.array([]), []
            
        texts = [chunk["text"] for chunk in chunks]
        
        # Use sentence-transformers to encode the texts directly
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            
        return embeddings, chunks
