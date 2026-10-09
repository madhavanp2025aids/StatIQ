import re

class Cleaner:
    """Utility to clean and normalize text before chunking and embedding."""

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Normalize text:
        - Remove extra whitespace
        - Standardize newlines
        - Remove non-printable characters (except standard whitespace)
        """
        if not text:
            return ""
            
        # Standardize newlines
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # Collapse multiple spaces, but keep structure for tables somewhat intact
        text = re.sub(r' {2,}', '  ', text)
        
        # Remove consecutive empty lines (more than 2)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove invisible/control characters except tab and newline
        text = re.sub(r'[^\x20-\x7E\t\n]', '', text)
        
        return text.strip()

    @staticmethod
    def clean_numerical_value(value: str) -> str:
        """
        Normalize a string that represents a number.
        E.g. ' 1,234.56 ' -> '1234.56'
        """
        if not isinstance(value, str):
            return str(value)
            
        # Remove spaces
        val = value.strip()
        # Remove commas if used as thousands separator
        val = val.replace(',', '')
        return val
