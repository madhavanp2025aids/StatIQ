import os
from typing import Dict, Any
from datetime import datetime

class MetadataExtractor:
    """Extracts and normalizes metadata for RAG chunks."""
    
    @staticmethod
    def extract_base_metadata(source_path: str, doc_type: str, custom_meta: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Creates the required base metadata dictionary.
        """
        meta = {
            "source": "MoSPI",
            "title": os.path.basename(source_path),
            "url": "", # Fill if known
            "document_type": doc_type, # e.g., 'official_report', 'dataset_json'
            "publication_date": "",
            "page": None,
            "section": "",
            "topic": "",
            "reference_year": "",
            "table_name": "",
            "document_id": source_path,
            "ingestion_date": datetime.now().isoformat()
        }
        
        if custom_meta:
            meta.update(custom_meta)
            
        return meta
