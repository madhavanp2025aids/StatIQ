import os
import sys
import argparse
import logging
from pathlib import Path

# Add project root to python path so we can import modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from knowledge.ingestion.pdf_loader import PDFLoader
from knowledge.embeddings.embedding_service import EmbeddingService
from knowledge.vector_store.faiss_store import FaissStore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ingest_pdf(pdf_path: str):
    """Ingests a PDF into the FAISS index."""
    if not os.path.exists(pdf_path):
        logger.error(f"File not found: {pdf_path}")
        return
        
    logger.info(f"Loading PDF {pdf_path}...")
    chunks = PDFLoader.load_mospi_pdf(pdf_path)
    
    if not chunks:
        logger.warning(f"No content extracted from {pdf_path}.")
        return
        
    logger.info(f"Extracted {len(chunks)} chunks. Generating embeddings...")
    embed_service = EmbeddingService.get_instance()
    
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    
    embeddings = embed_service.embed_batch(texts)
    
    logger.info("Adding to FAISS index...")
    faiss_store = FaissStore()
    faiss_store.add_documents(embeddings, metadatas)
    
    logger.info(f"Successfully ingested {pdf_path}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest a MoSPI PDF into the Knowledge Base.")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    args = parser.parse_args()
    
    ingest_pdf(args.pdf_path)
