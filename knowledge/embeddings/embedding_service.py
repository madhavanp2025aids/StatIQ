import os
from typing import List, Optional
from dotenv import load_dotenv

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

load_dotenv()

class EmbeddingService:
    """Service to generate embeddings using sentence-transformers."""
    
    _instance = None
    
    def __init__(self, model_name: Optional[str] = None):
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers is not installed. Please install it.")
        
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        # Load the model lazily
        self._model = None

    @classmethod
    def get_instance(cls) -> 'EmbeddingService':
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            print(f"Loading embedding model {self.model_name}...")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_text(self, text: str) -> List[float]:
        """Generate an embedding for a single text."""
        if not text.strip():
            # Return zero vector for empty text? Or handle upstream.
            # Assuming upstream handles it, but let's be safe.
            return [0.0] * 384 # Default dimension for all-MiniLM-L6-v2
        return self.model.encode(text).tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        if not texts:
            return []
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
