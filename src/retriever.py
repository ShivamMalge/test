import faiss
import numpy as np
import re
from typing import List, Dict, Any
from rank_bm25 import BM25Plus
from src.embeddings import EmbeddingPipeline

def _tokenize(text: str) -> List[str]:
    # Remove punctuation and split
    text = re.sub(r'[^\w\s]', '', text.lower())
    return text.split()

class Retriever:
    def __init__(self, embedding_pipeline: EmbeddingPipeline):
        self.embedding_pipeline = embedding_pipeline
        self.index = None
        self.bm25 = None
        self.chunks = []
        
    def build_index(self, embeddings: np.ndarray, chunks: List[Dict[str, Any]]):
        """
        Builds a FAISS index and BM25 index from the given embeddings and chunks.
        """
        if len(embeddings) == 0 or len(chunks) == 0:
            return
            
        dimension = embeddings.shape[1]
        
        # Initialize FAISS index for inner product (cosine similarity for normalized vectors)
        # We assume embeddings are normalized by SentenceTransformer.
        # If not perfectly normalized, IP still works better for ranking semantic similarity than raw L2 sometimes.
        # But we'll use IndexFlatL2 to be safe since we already tested it. 
        # Wait, actually L2 works fine, let's keep L2 to avoid breaking existing distance assumptions, 
        # but the scores sorting is what matters. 
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)
        
        # Initialize BM25 index using BM25Plus to avoid negative IDFs
        tokenized_corpus = [_tokenize(chunk["text"]) for chunk in chunks]
        self.bm25 = BM25Plus(tokenized_corpus)
        
        self.chunks = chunks
        
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Performs hybrid retrieval using FAISS and BM25, combined with RRF.
        """
        if self.index is None or self.index.ntotal == 0:
            return []
            
        # Ensure we retrieve enough candidates for re-ranking
        k = min(top_k * 3, self.index.ntotal)
        
        # 1. Semantic Search (FAISS)
        query_embeddings, _ = self.embedding_pipeline.embed_chunks([{"text": query}])
        distances, indices = self.index.search(query_embeddings, k)
        
        faiss_ranks = {}
        for rank, idx in enumerate(indices[0]):
            faiss_ranks[idx] = rank + 1
            
        # 2. Keyword Search (BM25)
        tokenized_query = _tokenize(query)
        bm25_scores = self.bm25.get_scores(tokenized_query)
        # Get top k indices for BM25
        bm25_indices = np.argsort(bm25_scores)[::-1][:k]
        
        bm25_ranks = {}
        for rank, idx in enumerate(bm25_indices):
            bm25_ranks[idx] = rank + 1
            
        # 3. Reciprocal Rank Fusion (RRF)
        # RRF_score = 1 / (k_rrf + rank)
        k_rrf = 60
        combined_scores = {}
        
        all_indices = set(faiss_ranks.keys()).union(set(bm25_ranks.keys()))
        
        for idx in all_indices:
            score = 0.0
            if idx in faiss_ranks:
                score += 1.0 / (k_rrf + faiss_ranks[idx])
            if idx in bm25_ranks:
                score += 1.0 / (k_rrf + bm25_ranks[idx])
            combined_scores[idx] = score
            
        # Sort by combined score descending
        sorted_indices = sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True)
        
        results = []
        for idx in sorted_indices[:top_k]:
            chunk = self.chunks[idx]
            results.append({
                "score": combined_scores[idx],
                "text": chunk["text"],
                "source": chunk["source"],
                "page": chunk["page"],
                "section": chunk["section"]
            })
            
        return results
