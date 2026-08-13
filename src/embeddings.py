import os
from typing import List, Dict, Any, Tuple
import numpy as np

class EmbeddingPipeline:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initializes the embedding pipeline.
        We default to 'all-MiniLM-L6-v2' as it is a lightweight, fast, and 
        capable model suitable for local RAG testing.
        """
        self.model_name = model_name
        # Lazy load to avoid slowing down import
        self.model = None

    def _load_model(self):
        if self.model is None:
            # We import here so we don't pay the import cost if we don't embed
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Embeds a list of chunks.
        
        Args:
            chunks: A list of chunk dictionaries.
            
        Returns:
            A tuple of (embeddings, chunks) where embeddings is a numpy array
            of shape (num_chunks, embedding_dim), and chunks is the list of 
            the original chunks in the exact same deterministic order, maintaining 
            the vector-to-chunk mapping.
        """
        if not chunks:
            return np.array([]), []
            
        self._load_model()
        
        texts = [chunk["text"] for chunk in chunks]
        
        # generate embeddings
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        
        return embeddings, chunks
