from typing import List, Dict, Any
from ..embeddings.embedding_service import EmbeddingService
from ..vector_store.faiss_store import FaissStore

class SemanticRetriever:
    """Retrieves chunks using semantic similarity."""

    def __init__(self, vector_store: FaissStore, embed_service: EmbeddingService):
        self.vector_store = vector_store
        self.embed_service = embed_service

    def retrieve(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Embeds the query and searches the vector store.
        Returns a list of dicts: {"metadata": {...}, "score": float}
        Note: For FAISS L2 distance, lower score is better. We will invert it
        or keep it as distance and handle it in the hybrid retriever.
        Let's convert L2 distance to a similarity score for consistency: similarity = 1 / (1 + distance)
        """
        query_embedding = self.embed_service.embed_text(query)
        results = self.vector_store.search(query_embedding, top_k=top_k)
        
        formatted_results = []
        for metadata, distance in results:
            # Convert L2 distance to a similarity score (0 to 1, higher is better)
            similarity = 1.0 / (1.0 + distance)
            
            formatted_results.append({
                "metadata": metadata,
                "score": similarity,
                "distance": distance
            })
            
        return formatted_results
