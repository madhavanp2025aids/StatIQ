"""Retrieval sub-package."""
import os
from pathlib import Path
from knowledge.vector_store.faiss_store import FaissStore
from knowledge.embeddings.embedding_service import EmbeddingService
from .semantic_retriever import SemanticRetriever
from .keyword_retriever import KeywordRetriever
from .hybrid_retriever import HybridRetriever

_hybrid_retriever_instance = None

def get_retriever() -> HybridRetriever:
    """Factory method to get the initialized HybridRetriever."""
    global _hybrid_retriever_instance
    if _hybrid_retriever_instance is None:
        # 1. Load FaissStore (which automatically loads metadata mapping)
        faiss_store = FaissStore()
        
        # 2. Setup Embedding Service
        embed_service = EmbeddingService.get_instance()
        
        # 3. Initialize base retrievers
        semantic_retriever = SemanticRetriever(faiss_store, embed_service)
        # Keyword retriever builds BM25 index on the fly from the faiss metadata
        keyword_retriever = KeywordRetriever(faiss_store.metadata_map)
        
        # 4. Create Hybrid Retriever
        _hybrid_retriever_instance = HybridRetriever(semantic_retriever, keyword_retriever)
        
    return _hybrid_retriever_instance
