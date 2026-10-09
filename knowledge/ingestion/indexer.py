import sys
from pathlib import Path
from typing import Dict, Any

# Add the project root to the python path so we can import backend and knowledge
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.data_loader import (
    get_plfs_raw, get_cpi_raw, get_nas_raw, get_iip_raw, get_asi_raw,
    get_literacy_raw, get_poverty_raw
)
from knowledge.vector_store.faiss_store import FaissStore
from knowledge.embeddings.embedding_service import EmbeddingService

def _stringify(record: Dict[str, Any]) -> str:
    """Converts a raw JSON record into a string representation for embedding/BM25."""
    parts = []
    for k, v in record.items():
        if k == '_dataset': continue
        parts.append(f"{k}: {v}")
    dataset_context = f"Dataset: {record.get('_dataset', 'unknown')} "
    return dataset_context + " | ".join(parts)

def main():
    print("Loading datasets...")
    datasets = {
        "plfs": get_plfs_raw(),
        "cpi": get_cpi_raw(),
        "nas": get_nas_raw(),
        "iip": get_iip_raw(),
        "asi": get_asi_raw(),
        "literacy": get_literacy_raw(),
        "poverty": get_poverty_raw(),
    }
    
    metadata_list = []
    texts = []
    
    for ds_name, ds_content in datasets.items():
        if not ds_content or "data" not in ds_content: continue
        records = ds_content["data"]
        for i, r in enumerate(records):
            # We want to preserve the original record fields in the metadata
            # plus add the dataset_name, year, etc. for QueryParser to use.
            meta = r.copy()
            meta["_dataset"] = ds_name
            meta["dataset_name"] = ds_name
            
            # Try to grab year/reference_year
            if "year" in r:
                meta["reference_year"] = str(r["year"])
                
            # Create the chunk_text
            chunk_text = _stringify(meta)
            meta["chunk_text"] = chunk_text
            meta["document_id"] = f"{ds_name}_{i}"
            
            metadata_list.append(meta)
            texts.append(chunk_text)
            
    print(f"Total records to index: {len(texts)}")
    print("Generating embeddings. This might take a few minutes...")
    
    embed_service = EmbeddingService.get_instance()
    
    # Process in batches to avoid memory issues with sentence-transformers if dataset is huge
    batch_size = 500
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        print(f"Embedding batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}...")
        batch_texts = texts[i:i+batch_size]
        batch_embs = embed_service.embed_batch(batch_texts)
        all_embeddings.extend(batch_embs)
        
    print("Building FAISS index...")
    faiss_store = FaissStore()
    faiss_store.add_documents(all_embeddings, metadata_list)
    
    print("Saving index and metadata to disk...")
    # FAISS store automatically saves on add_documents, but we can call it explicitly
    faiss_store.save()
    
    print("Done! Indexes are ready for retrieval.")

if __name__ == "__main__":
    main()
