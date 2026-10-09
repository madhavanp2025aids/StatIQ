from typing import List, Dict, Any
import logging

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

logger = logging.getLogger(__name__)

class KeywordRetriever:
    """Retrieves chunks using BM25 keyword matching."""

    def __init__(self, metadata_map: Dict[int, Dict[str, Any]]):
        self.metadata_map = metadata_map
        self.documents = []
        self.doc_ids = []
        self.bm25 = None
        
        self._build_index()

    def _build_index(self):
        """Builds the BM25 index from the metadata map."""
        if BM25Okapi is None:
            logger.warning("rank_bm25 is not installed. Keyword retrieval will be disabled.")
            return
            
        tokenized_corpus = []
        
        for doc_id, meta in self.metadata_map.items():
            text = meta.get("chunk_text", "")
            # Simple tokenization: lowercase and split by space
            tokens = text.lower().split()
            tokenized_corpus.append(tokens)
            self.documents.append(meta)
            self.doc_ids.append(doc_id)
            
        if tokenized_corpus:
            self.bm25 = BM25Okapi(tokenized_corpus)
            logger.info(f"Built BM25 index with {len(tokenized_corpus)} documents.")

    def retrieve(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves top_k documents using BM25.
        Returns a list of dicts: {"metadata": {...}, "score": float}
        """
        if self.bm25 is None or not self.documents:
            return []
            
        tokenized_query = query.lower().split()
        doc_scores = self.bm25.get_scores(tokenized_query)
        
        # Get top k indices
        top_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            score = float(doc_scores[idx])
            if score > 0:
                results.append({
                    "metadata": self.documents[idx],
                    "score": score
                })
                
        return results
