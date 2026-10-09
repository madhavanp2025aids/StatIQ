from typing import Dict, Any, List
from knowledge.retrieval import get_retriever

def smart_retrieve_rag(query: str, detected_datasets: List[str] = None) -> Dict[str, Any]:
    """
    RAG-based retrieve:
    Uses the HybridRetriever (FAISS + BM25) to get top K records relevant to the query.
    Falls back to empty if index not built.
    """
    try:
        retriever = get_retriever()
        # Ensure that FAISS and BM25 loaded properly
        if retriever.semantic.vector_store.index.ntotal == 0:
            return {"detected_datasets": detected_datasets or [], "data": {}}
    except Exception as e:
        print(f"Error loading retriever: {e}")
        return {"detected_datasets": detected_datasets or [], "data": {}}
        
    top_results = retriever.retrieve(query, top_k=20)
    
    # Organize records by dataset name for backward compatibility with agent.py
    data_by_ds = {}
    
    for res in top_results:
        # The actual record is in the metadata
        r = res["metadata"]
        ds_name = r.get('_dataset')
        if not ds_name: continue
        
        # If user explicitly filtered by dataset, we can optionally enforce it here.
        # But for RAG, the vector search already brings up the most semantically relevant.
        if detected_datasets and ds_name not in detected_datasets:
            pass 
        
        if ds_name not in data_by_ds:
            data_by_ds[ds_name] = {"meta": {}, "records": []}
        data_by_ds[ds_name]["records"].append(r)
        
    # We still need the meta for each dataset (from data_loader)
    from backend.data_loader import get_plfs_raw, get_cpi_raw, get_nas_raw, get_iip_raw, get_asi_raw, get_literacy_raw, get_poverty_raw
    meta_fetchers = {
        "plfs": get_plfs_raw,
        "cpi": get_cpi_raw,
        "nas": get_nas_raw,
        "iip": get_iip_raw,
        "asi": get_asi_raw,
        "literacy": get_literacy_raw,
        "poverty": get_poverty_raw,
    }
    
    for ds_name in list(data_by_ds.keys()):
        if ds_name in meta_fetchers:
            meta = meta_fetchers[ds_name]().get("meta", {})
            data_by_ds[ds_name]["meta"] = meta
            
    final_detected = list(data_by_ds.keys())
    # If the RAG found nothing that matches the original keyword filters, return the keyword filters
    if not final_detected and detected_datasets:
        final_detected = detected_datasets
        
    return {
        "detected_datasets": final_detected,
        "data": data_by_ds
    }
