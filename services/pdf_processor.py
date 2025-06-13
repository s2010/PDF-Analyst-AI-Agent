import logging
from typing import List
from pathlib import Path

import fitz  # PyMuPDF
from fastapi import HTTPException

from core.config import settings
from models.schemas import PageContent
from utils.file_utils import SecurityUtils

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Service for PDF text extraction and processing with security checks"""
    
    @staticmethod
    def extract_text_with_pages(pdf_path: str) -> List[PageContent]:
        """
        Extract text from PDF with page numbers and security validation
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List[PageContent]: List of page content objects
            
        Raises:
            HTTPException: If PDF processing fails
        """
        try:
            doc = fitz.open(pdf_path)
            pages_content = []
            
            # Limit processing to reasonable number of pages
            page_count = min(doc.page_count, settings.MAX_PDF_PAGES)
            
            for page_num in range(page_count):
                page = doc[page_num]
                text = page.get_text()
                
                if text.strip():  # Only add pages with content
                    # Sanitize extracted text
                    safe_text = SecurityUtils.sanitize_text(text)
                    
                    pages_content.append(PageContent(
                        page_number=page_num + 1,
                        content=safe_text.strip(),
                        char_count=len(safe_text)
                    ))
            
            doc.close()
            logger.info(f"Extracted text from {len(pages_content)} pages")
            return pages_content
            
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise HTTPException(
                status_code=400, 
                detail="Invalid PDF file or corrupted content"
            )
    
    @staticmethod
    def chunk_text(
        text: str, 
        chunk_size: int = None, 
        overlap: int = None
    ) -> List[str]:
        """
        Split text into overlapping chunks with size validation
        
        Args:
            text: Text content to chunk
            chunk_size: Size of each chunk (defaults to settings value)
            overlap: Overlap between chunks (defaults to settings value)
            
        Returns:
            List[str]: List of text chunks
        """
        chunk_size = chunk_size or settings.CHUNK_SIZE
        overlap = overlap or settings.CHUNK_OVERLAP
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text) and len(chunks) < settings.MAX_CHUNKS_PER_DOCUMENT:
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at word boundaries
            if end < len(text):
                last_space = chunk.rfind(' ')
                if last_space > chunk_size // 2:
                    chunk = chunk[:last_space]
                    end = start + last_space
            
            chunks.append(chunk.strip())
            start = end - overlap
            
            if start >= len(text):
                break
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks
    
    @classmethod
    def process_pdf(cls, pdf_path: str) -> tuple[List[str], List[dict]]:
        """
        Complete PDF processing pipeline: extract text and create chunks
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            tuple: (chunks, metadata) where chunks is list of text chunks
                   and metadata is list of corresponding metadata dicts
        """
        # Extract text with page numbers
        pages_content = cls.extract_text_with_pages(pdf_path)
        
        if not pages_content:
            raise HTTPException(
                status_code=400, 
                detail="No extractable text content found in PDF"
            )
        
        # Process each page into chunks
        all_chunks = []
        all_metadata = []
        
        for page_data in pages_content:
            chunks = cls.chunk_text(page_data.content)
            
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                # Note: metadata structure will be completed by the caller
                # with document-specific information like document_id, filename, etc.
                all_metadata.append({
                    "page_number": page_data.page_number,
                    "chunk_index": i,
                })
        
        logger.info(
            f"Processed PDF: {len(pages_content)} pages, {len(all_chunks)} chunks"
        )
        
        return all_chunks, all_metadata 