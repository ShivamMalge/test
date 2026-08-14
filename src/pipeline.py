import os
from typing import Dict, Any

from src.parser import parse_document
from src.parser_pypdf import parse_document_pypdf
from src.chunker import Chunker
from src.embeddings import EmbeddingPipeline
from src.retriever import Retriever
from src.generator import Generator

class LightningRAG:
    """
    The end-to-end RAG pipeline using LightningParse.
    """
    def __init__(self, 
                 max_chunk_size: int = 1000, 
                 embedding_model: str = "all-MiniLM-L6-v2",
                 llm_model: str = "google/gemini-2.5-flash",
                 parser_type: str = "lightningparse"):
        
        self.chunker = Chunker(max_chunk_size=max_chunk_size)
        self.embedding_pipeline = EmbeddingPipeline(model_name=embedding_model)
        self.retriever = Retriever(self.embedding_pipeline)
        self.generator = Generator(model=llm_model)
        self.parser_type = parser_type
        
        self.indexed_docs = set()

    def ingest_document(self, pdf_path: str):
        """
        Parses, chunks, embeds, and indexes a PDF document.
        """
        if pdf_path in self.indexed_docs:
            print(f"Document {pdf_path} is already indexed.")
            return
            
        print(f"Ingesting {pdf_path} using {self.parser_type}...")
        if self.parser_type == "pypdf":
            parsed_doc = parse_document_pypdf(pdf_path)
        else:
            parsed_doc = parse_document(pdf_path)
        
        print("Chunking...")
        chunks = self.chunker.chunk_document(parsed_doc, pdf_path)
        
        print("Embedding...")
        embeddings, chunks = self.embedding_pipeline.embed_chunks(chunks)
        
        print("Indexing...")
        # Note: In a real system we'd append to the index. 
        # Here we just build/rebuild the index for simplicity in v0.1.
        self.retriever.build_index(embeddings, chunks)
        
        self.indexed_docs.add(pdf_path)
        print(f"Successfully indexed {pdf_path} ({len(chunks)} chunks).")

    def ask(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Answers a question using the indexed documents.
        """
        if not self.indexed_docs:
            return {"answer": "No documents have been indexed yet.", "sources": []}
            
        # 1. Retrieve
        retrieved_chunks = self.retriever.search(question, top_k=top_k)
        
        # 2. Generate
        result = self.generator.generate(question, retrieved_chunks)
        
        return result

# Simple exposed functional API
_global_rag = None

def ask(pdf_path: str, question: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Convenience function to ingest a single PDF and ask a question.
    """
    global _global_rag
    if _global_rag is None:
        _global_rag = LightningRAG()
        
    _global_rag.ingest_document(pdf_path)
    return _global_rag.ask(question, top_k=top_k)
