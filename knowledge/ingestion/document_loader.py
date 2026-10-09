import json
from pathlib import Path
from typing import List, Dict, Any

from .metadata_extractor import MetadataExtractor
from ..processing.chunker import Chunker

class DocumentLoader:
    """Loads various document types and converts them to chunks for the RAG pipeline."""

    @staticmethod
    def load_mospi_json(file_path: str) -> List[Dict[str, Any]]:
        """
        Loads a MoSPI dataset JSON (e.g., cpi.json, plfs.json) and chunks each record.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        dataset_name = data.get('dataset', Path(file_path).stem.upper())
        full_name = data.get('full_name', '')
        
        base_meta = MetadataExtractor.extract_base_metadata(
            source_path=file_path,
            doc_type='dataset_json',
            custom_meta={
                'dataset_name': dataset_name,
                'title': full_name,
                'topic': dataset_name,
                'url': 'https://mospi.gov.in', # Default placeholder
            }
        )
        
        records = data.get('data', [])
        chunks = []
        
        for record in records:
            record_chunks = Chunker.chunk_structured_record(record, base_meta)
            chunks.extend(record_chunks)
            
        return chunks
