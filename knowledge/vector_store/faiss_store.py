import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

try:
    import faiss
    import numpy as np
except ImportError:
    faiss = None
    np = None

logger = logging.getLogger(__name__)

class FaissStore:
    """Manages the FAISS vector database and metadata mapping."""
    
    def __init__(self, index_path: str = None, meta_path: str = None, dimension: int = 384):
        if faiss is None or np is None:
            raise ImportError("faiss-cpu and numpy are required. Please install them.")
            
        # Default paths if not provided
        base_dir = Path(__file__).parent.parent / "db"
        
        self.index_path = Path(index_path or os.getenv("FAISS_INDEX_PATH", base_dir / "faiss.index"))
        self.meta_path = Path(meta_path or os.getenv("FAISS_META_PATH", base_dir / "metadata.json"))
        self.dimension = dimension
        
        self.index = None
        # metadata mapping: integer id -> dictionary of metadata (including original text chunk)
        self.metadata_map: Dict[int, Dict[str, Any]] = {}
        self.next_id = 0
        
        # Ensure directories exist
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.load()

    def load(self):
        """Load index and metadata from disk if they exist, otherwise initialize new ones."""
        if self.index_path.exists() and self.meta_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path))
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    meta_data = json.load(f)
                    # JSON keys are strings, convert back to int
                    self.metadata_map = {int(k): v for k, v in meta_data.items()}
                
                if self.metadata_map:
                    self.next_id = max(self.metadata_map.keys()) + 1
                else:
                    self.next_id = 0
                    
                logger.info(f"Loaded FAISS index from {self.index_path} with {self.index.ntotal} vectors.")
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}. Creating new index.")
                self._init_new_index()
        else:
            self._init_new_index()

    def _init_new_index(self):
        """Initialize a new FAISS IndexFlatL2."""
        # IndexFlatL2 is simple and exact (L2 distance). 
        # For cosine similarity, vectors should be normalized before adding, 
        # or we could use IndexFlatIP (Inner Product) with normalized vectors.
        # We will use IndexFlatL2 for simplicity, but normalize embeddings in the embedding step for better semantic search.
        self.index = faiss.IndexIDMap(faiss.IndexFlatL2(self.dimension))
        self.metadata_map = {}
        self.next_id = 0
        logger.info("Initialized new FAISS index.")

    def save(self):
        """Save index and metadata to disk."""
        faiss.write_index(self.index, str(self.index_path))
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata_map, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved FAISS index to {self.index_path}.")

    def add_documents(self, embeddings: List[List[float]], metadata_list: List[Dict[str, Any]]):
        """
        Add new documents to the index.
        
        Args:
            embeddings: List of embedding vectors.
            metadata_list: List of metadata dictionaries corresponding to each embedding.
        """
        if not embeddings or not metadata_list:
            return
            
        if len(embeddings) != len(metadata_list):
            raise ValueError("Number of embeddings must match number of metadata dicts.")
            
        # Convert to numpy array of float32
        vectors = np.array(embeddings, dtype=np.float32)
        
        # Generate IDs
        ids = np.arange(self.next_id, self.next_id + len(embeddings), dtype=np.int64)
        
        # Add to index
        self.index.add_with_ids(vectors, ids)
        
        # Add to metadata map
        for i, meta in enumerate(metadata_list):
            self.metadata_map[int(ids[i])] = meta
            
        self.next_id += len(embeddings)
        self.save()

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search the index for the most similar vectors.
        
        Args:
            query_embedding: The embedding vector of the query.
            top_k: Number of results to return.
            
        Returns:
            List of tuples: (metadata_dict, l2_distance_score)
        """
        if self.index.ntotal == 0:
            return []
            
        # Limit top_k to the number of elements in the index
        k = min(top_k, self.index.ntotal)
        
        # Reshape query to (1, dimension)
        query_vector = np.array([query_embedding], dtype=np.float32)
        
        # Search
        distances, indices = self.index.search(query_vector, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and int(idx) in self.metadata_map:
                meta = self.metadata_map[int(idx)]
                distance = float(distances[0][i])
                results.append((meta, distance))
                
        return results
