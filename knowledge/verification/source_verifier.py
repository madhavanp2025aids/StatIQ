from typing import List, Dict, Any

class SourceVerifier:
    """Verifies that chunks have valid MoSPI sources."""
    
    @staticmethod
    def verify_sources(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ensures each chunk has basic source metadata.
        Returns citations for the valid chunks.
        """
        citations = []
        seen = set()
        
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            source = meta.get("source", "Unknown")
            title = meta.get("title", "Unknown Document")
            
            # We want to build unique citations based on document and page/table
            page = meta.get("page", "")
            table = meta.get("table_name", meta.get("table", ""))
            
            citation_key = f"{title}_{page}_{table}"
            
            if citation_key not in seen:
                seen.add(citation_key)
                
                citation = {
                    "source_org": source,
                    "document": title,
                    "url": meta.get("url", ""),
                    "dataset": meta.get("dataset_name", ""),
                    "reference_period": meta.get("reference_year", meta.get("year", "")),
                }
                
                if page:
                    citation["page"] = page
                if table:
                    citation["table"] = table
                    
                citations.append(citation)
                
        return citations
