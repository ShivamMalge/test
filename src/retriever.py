import faiss
import numpy as np
from typing import List, Dict, Any
from src.embeddings import EmbeddingPipeline

class Retriever:
    def __init__(self, embedding_pipeline: EmbeddingPipeline):
        self.embedding_pipeline = embedding_pipeline
        self.index = None
        self.chunks = []
        
    def build_index(self, embeddings: np.ndarray, chunks: List[Dict[str, Any]]):
        """
        Builds a FAISS index from the given embeddings and stores the corresponding chunks.
        """
        if len(embeddings) == 0:
            return
            
        dimension = embeddings.shape[1]
        
        # Initialize an L2 distance (or Inner Product) index.
        # all-MiniLM-L6-v2 embeddings are often normalized, but L2 works fine for cosine distance equivalent.
        self.index = faiss.IndexFlatL2(dimension)
        
        # Add vectors
        self.index.add(embeddings)
        self.chunks = chunks
        
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Embeds the query and searches the FAISS index for top_k closest chunks.
        
        Returns:
            A list of retrieval results with metadata.
        """
        if self.index is None or self.index.ntotal == 0:
            return []
            
        # Ensure k is not larger than available chunks
        k = min(top_k, self.index.ntotal)
        
        # Embed query
        # We reuse the pipeline but format the input as a dummy chunk list
        query_embeddings, _ = self.embedding_pipeline.embed_chunks([{"text": query}])
        
        # Search
        distances, indices = self.index.search(query_embeddings, k)
        
        results = []
        for i in range(k):
            idx = indices[0][i]
            dist = float(distances[0][i])
            
            chunk = self.chunks[idx]
            
            # Format the output as specified
            results.append({
                "score": dist,
                "text": chunk["text"],
                "source": chunk["source"],
                "page": chunk["page"],
                "section": chunk["section"]
            })
            
        return results
