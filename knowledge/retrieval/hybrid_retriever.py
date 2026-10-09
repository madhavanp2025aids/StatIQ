from typing import List, Dict, Any
from .semantic_retriever import SemanticRetriever
from .keyword_retriever import KeywordRetriever
from .query_parser import QueryParser

class HybridRetriever:
    """Combines semantic and keyword retrieval using Reciprocal Rank Fusion."""

    def __init__(self, semantic_retriever: SemanticRetriever, keyword_retriever: KeywordRetriever):
        self.semantic = semantic_retriever
        self.keyword = keyword_retriever

    def retrieve(self, query: str, top_k: int = 10, rrf_k: int = 60) -> List[Dict[str, Any]]:
        """
        Retrieves using both methods and fuses ranks.
        rrf_k is the smoothing constant for Reciprocal Rank Fusion (standard is 60).
        """
        # Parse query for entities to potentially boost certain chunks (metadata filtering could also go here)
        entities = QueryParser.extract_entities(query)
        
        # Get more than top_k from base retrievers to ensure good fusion coverage
        base_k = top_k * 2
        
        sem_results = self.semantic.retrieve(query, top_k=base_k)
        kw_results = self.keyword.retrieve(query, top_k=base_k)
        
        # Map to keep track of scores by document ID/Text
        # Using a hash of chunk_text as a unique ID since we didn't strictly carry FAISS ID everywhere
        # Or better: chunk_text itself since it's unique enough for our purposes
        fused_scores = {}
        doc_metadata = {}
        
        def get_doc_id(meta):
            # Fallback to chunk text if no explicit ID
            return meta.get("document_id", "") + "_" + str(meta.get("chunk_index", meta.get("chunk_text", "")[:50]))

        # Apply Reciprocal Rank Fusion
        for rank, res in enumerate(sem_results):
            doc_id = get_doc_id(res["metadata"])
            doc_metadata[doc_id] = res["metadata"]
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0.0
            fused_scores[doc_id] += 1.0 / (rrf_k + rank + 1)
            
        for rank, res in enumerate(kw_results):
            doc_id = get_doc_id(res["metadata"])
            doc_metadata[doc_id] = res["metadata"]
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0.0
            fused_scores[doc_id] += 1.0 / (rrf_k + rank + 1)
            
        # Boost exact entity matches
        # e.g., if query has year "2023", boost chunks that have "2023" in year metadata
        for doc_id, meta in doc_metadata.items():
            boost = 0.0
            if entities["years"]:
                # Check if any query year matches document reference year
                doc_year = str(meta.get("reference_year", meta.get("year", "")))
                if any(y in doc_year for y in entities["years"]):
                    boost += 0.05
                    
            if entities["indicators"]:
                doc_ds = str(meta.get("dataset_name", meta.get("topic", ""))).lower()
                if any(ind in doc_ds for ind in entities["indicators"]):
                    boost += 0.05
                    
            fused_scores[doc_id] += boost

        # Sort by fused score
        sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Format top_k
        final_results = []
        for doc_id, score in sorted_results[:top_k]:
            final_results.append({
                "metadata": doc_metadata[doc_id],
                "score": score
            })
            
        return final_results
