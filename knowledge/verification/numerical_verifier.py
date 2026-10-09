import pandas as pd
from typing import Dict, Any, List

class NumericalVerifier:
    """Verifies numerical claims or performs simple calculations using Pandas."""
    
    @staticmethod
    def calculate_percentage_change(old_value: float, new_value: float) -> float:
        if old_value == 0:
            return 0.0
        return ((new_value - old_value) / old_value) * 100.0

    @staticmethod
    def verify_values(chunks: List[Dict[str, Any]], query_type: str) -> Dict[str, Any]:
        """
        Attempts to extract verified numbers from structured chunks.
        Since our structured chunks contain the actual JSON data, we can just 
        extract those explicitly to pass to the LLM.
        """
        verified_data = []
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            # If it's a structured dataset record, it will have fields like 'General', 'Food', 'year', 'month'
            if "dataset_name" in meta:
                # Keep a simplified version of the record
                clean_record = {k: v for k, v in meta.items() if k not in ["chunk_text", "chunk_index"]}
                verified_data.append(clean_record)
                
        return {
            "structured_records": verified_data,
            "has_numerical_data": len(verified_data) > 0
        }
