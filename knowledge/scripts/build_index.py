import os
import sys
import logging
from pathlib import Path

# Add project root to python path so we can import modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from knowledge.ingestion.document_loader import DocumentLoader
from knowledge.embeddings.embedding_service import EmbeddingService
from knowledge.vector_store.faiss_store import FaissStore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def build_initial_index():
    """Builds the FAISS index from the existing JSON datasets."""
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    
    datasets = ["cpi.json", "plfs.json", "nas.json", "iip.json", "asi.json"]
    
    all_chunks = []
    for dataset in datasets:
        file_path = data_dir / dataset
        if file_path.exists():
            logger.info(f"Loading {dataset}...")
            chunks = DocumentLoader.load_mospi_json(str(file_path))
            all_chunks.extend(chunks)
            logger.info(f"Loaded {len(chunks)} chunks from {dataset}.")
        else:
            logger.warning(f"Dataset {dataset} not found at {file_path}")
            
    if not all_chunks:
        logger.error("No chunks loaded. Aborting.")
        return
        
    logger.info(f"Total chunks loaded: {len(all_chunks)}. Initializing embedding model...")
    embed_service = EmbeddingService.get_instance()
    
    # Process in batches
    batch_size = 64
    faiss_store = FaissStore()
    
    logger.info("Generating embeddings and adding to FAISS...")
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i+batch_size]
        texts = [c["text"] for c in batch]
        metadatas = [c["metadata"] for c in batch]
        
        embeddings = embed_service.embed_batch(texts)
        faiss_store.add_documents(embeddings, metadatas)
        
        logger.info(f"Processed batch {i//batch_size + 1}/{(len(all_chunks)-1)//batch_size + 1}")
        
    logger.info("Finished building index.")

if __name__ == "__main__":
    build_initial_index()
