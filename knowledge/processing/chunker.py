import json
from typing import List, Dict, Any

class Chunker:
    """Chunks documents into pieces for the vector store."""

    @staticmethod
    def chunk_structured_record(record: Dict[str, Any], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Takes a single row/record from a structured dataset (like PLFS, CPI JSON)
        and converts it into a single chunk.
        
        Args:
            record: The raw data record (e.g. one row of CPI data).
            metadata: Base metadata (source, topic, etc.).
            
        Returns:
            A list containing a single chunk dictionary with text and metadata.
        """
        # We don't chunk structured records further; the whole record is one semantic unit.
        
        # Format the text representation for embedding. We want keywords to be prominent.
        # e.g., "CPI Inflation for January 2024: General 213.7, Food 222.5. YoY: 5.10%"
        
        # Create a readable text block. We just dump JSON for simplicity and accuracy, 
        # but prefixed with dataset name and year/period if available to give context to embeddings.
        ds_name = metadata.get('dataset_name', '')
        year = record.get('year', metadata.get('reference_year', ''))
        
        prefix = f"Dataset: {ds_name}. Year/Period: {year}. Data record:\n"
        
        text_content = prefix + json.dumps(record, indent=2)
        
        # Merge record keys into metadata for filtering
        chunk_meta = metadata.copy()
        for k, v in record.items():
            if k not in chunk_meta and isinstance(v, (str, int, float, bool)):
                chunk_meta[k] = v
                
        chunk_meta["chunk_text"] = text_content
        
        return [{
            "text": text_content,
            "metadata": chunk_meta
        }]

    @staticmethod
    def chunk_text(text: str, metadata: Dict[str, Any], max_words: int = 200, overlap: int = 50) -> List[Dict[str, Any]]:
        """
        Splits plain text into chunks with overlap.
        """
        words = text.split()
        chunks = []
        
        if not words:
            return chunks
            
        i = 0
        chunk_index = 0
        while i < len(words):
            chunk_words = words[i:i + max_words]
            chunk_text = " ".join(chunk_words)
            
            chunk_meta = metadata.copy()
            chunk_meta["chunk_index"] = chunk_index
            chunk_meta["chunk_text"] = chunk_text
            
            chunks.append({
                "text": chunk_text,
                "metadata": chunk_meta
            })
            
            i += (max_words - overlap)
            chunk_index += 1
            
        return chunks
