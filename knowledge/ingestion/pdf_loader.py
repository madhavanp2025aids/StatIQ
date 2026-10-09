import logging
from typing import List, Dict, Any
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from .metadata_extractor import MetadataExtractor
from ..processing.chunker import Chunker
from ..processing.cleaner import Cleaner

logger = logging.getLogger(__name__)

class PDFLoader:
    """Loads PDF documents using PyMuPDF."""

    @staticmethod
    def load_mospi_pdf(file_path: str) -> List[Dict[str, Any]]:
        """
        Loads a MoSPI PDF publication, extracts text and tables, and chunks it.
        """
        if fitz is None:
            logger.error("PyMuPDF is not installed. Cannot load PDFs.")
            return []
            
        try:
            doc = fitz.open(file_path)
        except Exception as e:
            logger.error(f"Failed to open PDF {file_path}: {e}")
            return []
            
        base_meta = MetadataExtractor.extract_base_metadata(
            source_path=file_path,
            doc_type='official_report',
            custom_meta={
                'title': Path(file_path).name,
            }
        )
        
        chunks = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            cleaned_text = Cleaner.clean_text(text)
            if not cleaned_text:
                continue
                
            page_meta = base_meta.copy()
            page_meta['page'] = page_num + 1
            
            # Simple text chunking for now (tables could be handled specifically in future iterations)
            page_chunks = Chunker.chunk_text(cleaned_text, page_meta, max_words=200, overlap=50)
            chunks.extend(page_chunks)
            
        return chunks
