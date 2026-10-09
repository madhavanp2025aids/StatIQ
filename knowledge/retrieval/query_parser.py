import re
from typing import Dict, Any, List

class QueryParser:
    """Classifies queries and extracts entities to improve retrieval."""

    # Pre-defined categories
    FACTUAL_STATISTICAL_QUERY = "FACTUAL_STATISTICAL_QUERY"
    COMPARISON_QUERY = "COMPARISON_QUERY"
    TREND_QUERY = "TREND_QUERY"
    DEFINITION_QUERY = "DEFINITION_QUERY"
    DATASET_QUERY = "DATASET_QUERY"
    REPORT_QUERY = "REPORT_QUERY"
    CALCULATION_QUERY = "CALCULATION_QUERY"
    GENERAL_QUERY = "GENERAL_QUERY"

    @staticmethod
    def classify_query(query: str) -> str:
        q = query.lower()
        
        if any(w in q for w in ["compare", "versus", "vs", "difference between", "higher", "lower"]):
            return QueryParser.COMPARISON_QUERY
            
        if any(w in q for w in ["trend", "history", "over time", "from", "to", "between"]):
            # "between year and year" could be trend or comparison. 
            # Simple heuristic: if it asks for trend specifically, it's trend.
            if "trend" in q or "over time" in q:
                return QueryParser.TREND_QUERY
                
        if any(w in q for w in ["what is", "define", "definition of", "meaning of"]):
            # Differentiate "what is CPI" vs "what is the CPI rate"
            if "rate" not in q and "in" not in q and "for" not in q:
                return QueryParser.DEFINITION_QUERY
                
        if any(w in q for w in ["calculate", "percentage change", "growth rate", "average"]):
            return QueryParser.CALCULATION_QUERY
            
        if any(w in q for w in ["which dataset", "where can i find", "datasets available"]):
            return QueryParser.DATASET_QUERY
            
        if any(w in q for w in ["report", "publication", "document"]):
            return QueryParser.REPORT_QUERY

        # If it asks for a specific value
        if any(w in q for w in ["what was", "what is the", "how much", "how many", "rate", "index", "value"]):
            return QueryParser.FACTUAL_STATISTICAL_QUERY
            
        return QueryParser.GENERAL_QUERY

    @staticmethod
    def extract_entities(query: str) -> Dict[str, Any]:
        """Extracts key entities like years, months, indicators."""
        q = query.lower()
        entities = {
            "years": [],
            "months": [],
            "indicators": [],
            "geography": None,
            "gender": None
        }
        
        # Years (e.g., 2023, 2023-24)
        years = re.findall(r'\b(20\d{2}(?:-\d{2})?)\b', q)
        if years:
            entities["years"] = years
            
        # Months
        months = ["january", "february", "march", "april", "may", "june", 
                  "july", "august", "september", "october", "november", "december",
                  "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        found_months = [m for m in months if re.search(r'\b' + m + r'\b', q)]
        if found_months:
            entities["months"] = found_months
            
        # Indicators
        indicators = ["cpi", "inflation", "gdp", "gva", "iip", "unemployment", "lfpr", "wpr", "asi"]
        for ind in indicators:
            if ind in q:
                entities["indicators"].append(ind)
                
        # Geography
        if "rural" in q:
            entities["geography"] = "rural"
        elif "urban" in q:
            entities["geography"] = "urban"
            
        # Gender
        if re.search(r'\bfemale\b|\bwomen\b', q):
            entities["gender"] = "female"
        elif re.search(r'\bmale\b|\bmen\b', q):
            entities["gender"] = "male"
            
        return entities
