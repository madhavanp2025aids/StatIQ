import os
from typing import Dict, Any, Tuple
import logging

from .embeddings.embedding_service import EmbeddingService
from .vector_store.faiss_store import FaissStore
from .retrieval.query_parser import QueryParser
from .retrieval.semantic_retriever import SemanticRetriever
from .retrieval.keyword_retriever import KeywordRetriever
from .retrieval.hybrid_retriever import HybridRetriever
from .verification.numerical_verifier import NumericalVerifier
from .verification.source_verifier import SourceVerifier
from .verification.confidence_checker import ConfidenceChecker

logger = logging.getLogger(__name__)

class KnowledgeService:
    """Orchestrates the entire RAG pipeline."""

    _instance = None

    def __init__(self):
        try:
            self.embed_service = EmbeddingService.get_instance()
            self.vector_store = FaissStore()
            
            self.semantic_retriever = SemanticRetriever(self.vector_store, self.embed_service)
            self.keyword_retriever = KeywordRetriever(self.vector_store.metadata_map)
            
            self.hybrid_retriever = HybridRetriever(self.semantic_retriever, self.keyword_retriever)
        except Exception as e:
            logger.error(f"Failed to initialize KnowledgeService: {e}")
            self.hybrid_retriever = None

    @classmethod
    def get_instance(cls) -> 'KnowledgeService':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def retrieve(self, query: str) -> Dict[str, Any]:
        """
        Executes the RAG pipeline for a given query.
        Returns:
            evidence (str): Formatted context for the LLM
            citations (List[Dict]): Source citations
            confidence (str): HIGH, MEDIUM, LOW
            query_type (str): The classified query type
            verified_data (Dict): Structured verified numerical data
        """
        if not self.hybrid_retriever:
            return self._fallback_empty()
            
        # 1. Query Parsing
        query_type = QueryParser.classify_query(query)
        entities = QueryParser.extract_entities(query)
        
        # 2. Hybrid Retrieval
        top_k = int(os.getenv("RAG_TOP_K", "8"))
        chunks = self.hybrid_retriever.retrieve(query, top_k=top_k)
        
        if not chunks:
            return self._fallback_empty(query_type)
            
        # 3. Verification & Grounding
        # Get actual structured data for numerical verification
        verification_result = NumericalVerifier.verify_values(chunks, query_type)
        
        # Extract citations
        citations = SourceVerifier.verify_sources(chunks)
        
        # Calculate confidence
        confidence = ConfidenceChecker.evaluate_confidence(chunks, entities)
        
        # 4. Evidence Builder
        evidence = self._build_evidence_string(chunks, verification_result)
        
        return {
            "evidence": evidence,
            "citations": citations,
            "confidence": confidence,
            "query_type": query_type,
            "verified_data": verification_result.get("structured_records", [])
        }

    def _build_evidence_string(self, chunks: list, verification: dict) -> str:
        """Formats the retrieved chunks into a string for the LLM prompt."""
        evidence_parts = []
        
        # Prioritize verified structured records
        structured = verification.get("structured_records", [])
        if structured:
            evidence_parts.append("=== VERIFIED OFFICIAL DATA ===")
            for record in structured:
                # Remove large text blocks from record just for prompt conciseness
                clean_rec = {k:v for k,v in record.items() if not isinstance(v, str) or len(v) < 100}
                evidence_parts.append(str(clean_rec))
                
        # Add textual chunks
        text_chunks = [c for c in chunks if "chunk_text" in c["metadata"]]
        if text_chunks:
            evidence_parts.append("\n=== RELEVANT DOCUMENTS ===")
            for i, chunk in enumerate(text_chunks):
                meta = chunk["metadata"]
                source = meta.get("source", "Unknown")
                title = meta.get("title", "Unknown")
                text = meta.get("chunk_text", "")
                
                evidence_parts.append(f"[Source {i+1}: {source} - {title}]\n{text}\n")
                
        return "\n".join(evidence_parts)

    def _fallback_empty(self, query_type: str = "GENERAL_QUERY") -> Dict[str, Any]:
        return {
            "evidence": "No official MoSPI evidence found in the knowledge base.",
            "citations": [],
            "confidence": "LOW",
            "query_type": query_type,
            "verified_data": []
        }
