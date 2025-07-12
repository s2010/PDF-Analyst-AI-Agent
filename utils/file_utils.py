import hashlib
import mimetypes
from fastapi import UploadFile


class SecurityUtils:
    """Security utility functions for file validation"""
    
    @staticmethod
    def validate_pdf_file(file: UploadFile) -> bool:
        """
        Validate PDF file type and content
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            bool: True if valid PDF
        """
        # Check file extension
        if not file.filename.lower().endswith('.pdf'):
            return False
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(file.filename)
        if mime_type != 'application/pdf':
            return False
        
        return True
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for safe file system operations
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
        sanitized = ''.join(c for c in filename if c in safe_chars)
        return sanitized[:255]  # Limit length
    
    @staticmethod
    def calculate_file_hash(content: bytes) -> str:
        """
        Calculate SHA-256 hash of file content
        
        Args:
            content: File content as bytes
            
        Returns:
            str: SHA-256 hash in hexadecimal
        """
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Sanitize text content to remove harmful characters
        
        Args:
            text: Raw text content
            
        Returns:
            str: Sanitized text
        """
        return ''.join(char for char in text if char.isprintable() or char.isspace())


class FileUtils:
    """File utility functions"""
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human readable format
        
        Args:
            size_bytes: File size in bytes
            
        Returns:
            str: Formatted file size
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def validate_file_size(content: bytes, max_size: int) -> bool:
        """
        Validate file size against maximum
        
        Args:
            content: File content as bytes
            max_size: Maximum allowed size in bytes
            
        Returns:
            bool: True if within limits
        """
        return len(content) <= max_size and len(content) > 0 