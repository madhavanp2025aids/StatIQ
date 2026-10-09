from typing import List, Dict, Any
import os

class ConfidenceChecker:
    """Evaluates the confidence of the retrieved evidence."""

    @staticmethod
    def evaluate_confidence(chunks: List[Dict[str, Any]], query_entities: Dict[str, Any]) -> str:
        """
        Returns 'HIGH', 'MEDIUM', or 'LOW' confidence.
        """
        if not chunks:
            return "LOW"
            
        min_threshold = float(os.getenv("RAG_MIN_CONFIDENCE", "0.3"))
        
        # Check top score
        top_score = chunks[0].get("score", 0.0)
        
        # Check if we found structured numerical data
        has_official_source = any(c.get("metadata", {}).get("source", "") == "MoSPI" for c in chunks)
        
        # Check if requested entities (like year) are present in metadata
        year_match = True
        if query_entities.get("years"):
            year_match = False
            for c in chunks:
                doc_year = str(c.get("metadata", {}).get("reference_year", c.get("metadata", {}).get("year", "")))
                if any(y in doc_year for y in query_entities["years"]):
                    year_match = True
                    break
                    
        # Decision Logic
        if top_score > min_threshold and has_official_source and year_match:
            # If the score is very high, it's HIGH confidence
            if top_score > (min_threshold * 1.5):
                return "HIGH"
            return "MEDIUM"
            
        if top_score <= min_threshold or not has_official_source:
            return "LOW"
            
        return "MEDIUM"
