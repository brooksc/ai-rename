import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import fitz  # PyMuPDF
import pdfplumber
from datetime import datetime
import pytesseract
from PIL import Image
import tempfile
from ..utils.logging import ProcessingError
from ..llm.provider import LLMProvider

class PDFProcessor:
    def __init__(self, config: Dict[str, Any], llm_provider: LLMProvider):
        """Initialize PDF processor with configuration and LLM provider."""
        self.config = config
        self.llm = llm_provider
        self.temp_dir = Path(config['paths']['temp'])
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def process_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Process a PDF file to extract text, metadata, and generate summaries.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict containing extracted information and processing results
        """
        try:
            # Calculate file hash
            file_hash = self._calculate_hash(file_path)
            
            # Extract text and basic metadata
            text, basic_metadata = self._extract_text_and_metadata(file_path)
            
            # Process with OCR if needed
            if not text and self.config['processing']['ocr_enabled']:
                text = self._perform_ocr(file_path)

            if not text:
                raise ProcessingError(f"No text could be extracted from {file_path}")

            # Process with LLM
            results = self._process_with_llm(text)
            
            return {
                'hash': file_hash,
                'text': text,
                'metadata': {**basic_metadata, **results.get('metadata', {})},
                'summary': results.get('summary'),
                'tags': results.get('tags', []),
                'categories': results.get('categories', [])
            }

        except Exception as e:
            raise ProcessingError(f"Failed to process PDF {file_path}: {e}")

    def _calculate_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file."""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            raise ProcessingError(f"Failed to calculate file hash: {e}")

    def _extract_text_and_metadata(self, file_path: str) -> tuple[str, Dict[str, Any]]:
        """Extract text and basic metadata from PDF."""
        text = ""
        metadata = {}
        
        try:
            # Try PyMuPDF first
            doc = fitz.open(file_path)
            try:
                # Extract metadata
                metadata = {
                    'title': doc.metadata.get('title', ''),
                    'author': doc.metadata.get('author', ''),
                    'subject': doc.metadata.get('subject', ''),
                    'keywords': doc.metadata.get('keywords', ''),
                    'creator': doc.metadata.get('creator', ''),
                    'producer': doc.metadata.get('producer', ''),
                    'creation_date': doc.metadata.get('creationDate', ''),
                    'modification_date': doc.metadata.get('modDate', ''),
                    'page_count': len(doc)
                }
                
                # Extract text
                for page in doc:
                    text += page.get_text()
                
            finally:
                doc.close()

            # If no text was extracted, try pdfplumber
            if not text.strip():
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or ''

            return text.strip(), metadata

        except Exception as e:
            logging.warning(f"Failed to extract text/metadata: {e}")
            return "", {}

    def _perform_ocr(self, file_path: str) -> str:
        """Perform OCR on PDF pages."""
        try:
            doc = fitz.open(file_path)
            text = ""
            
            for page_num in range(len(doc)):
                # Get page as image
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                
                # Save to temporary image file
                img_path = self.temp_dir / f"page_{page_num}.png"
                pix.save(str(img_path))
                
                # Perform OCR
                try:
                    with Image.open(img_path) as img:
                        page_text = pytesseract.image_to_string(img)
                        text += page_text + "\n\n"
                finally:
                    img_path.unlink(missing_ok=True)
            
            return text.strip()

        except Exception as e:
            logging.warning(f"OCR processing failed: {e}")
            return ""

    def _process_with_llm(self, text: str) -> Dict[str, Any]:
        """Process extracted text with LLM for various analyses."""
        results = {}
        
        try:
            # Generate summary
            summary_result = self.llm.process_text(
                text[:self.config['llm']['max_chunk_size']],
                'summarize'
            )
            results['summary'] = summary_result['content']

            # Extract metadata
            metadata_result = self.llm.process_text(
                text[:self.config['llm']['max_chunk_size']],
                'extract_metadata'
            )
            try:
                results['metadata'] = json.loads(metadata_result['content'])
            except json.JSONDecodeError:
                logging.warning("Failed to parse metadata JSON from LLM")
                results['metadata'] = {}

            # Generate tags
            if self.config['llm']['tag_generation']:
                tag_result = self.llm.process_text(text, 'tag')
                results['tags'] = [t.strip() for t in tag_result['content'].split(',')]

            # Generate categories
            if self.config['llm']['auto_categorize']:
                cat_result = self.llm.process_text(text, 'categorize')
                results['categories'] = [c.strip() for c in cat_result['content'].split(',')]

        except Exception as e:
            logging.error(f"LLM processing failed: {e}")

        return results

    def cleanup(self) -> None:
        """Clean up temporary files."""
        try:
            for file in self.temp_dir.glob("page_*.png"):
                file.unlink(missing_ok=True)
        except Exception as e:
            logging.warning(f"Cleanup failed: {e}")
