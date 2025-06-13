import hashlib
import mimetypes
from fastapi import UploadFile


class SecurityUtils:
    """Security utility functions for file validation and sanitization"""
    
    @staticmethod
    def validate_pdf_file(file: UploadFile) -> bool:
        """
        Validate PDF file type and content
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            bool: True if file is valid PDF, False otherwise
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
        Sanitize filename to prevent directory traversal and other security issues
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename safe for file system operations
        """
        # Remove path components and special characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
        sanitized = ''.join(c for c in filename if c in safe_chars)
        return sanitized[:255]  # Limit length to prevent filesystem issues
    
    @staticmethod
    def calculate_file_hash(content: bytes) -> str:
        """
        Calculate SHA-256 hash of file content for integrity verification
        
        Args:
            content: File content as bytes
            
        Returns:
            str: SHA-256 hash in hexadecimal format
        """
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Sanitize extracted text content to remove potentially harmful characters
        
        Args:
            text: Raw text content
            
        Returns:
            str: Sanitized text with only printable characters and whitespace
        """
        return ''.join(char for char in text if char.isprintable() or char.isspace())


class FileUtils:
    """General file utility functions"""
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human readable format
        
        Args:
            size_bytes: File size in bytes
            
        Returns:
            str: Formatted file size (e.g., "1.5 MB")
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
        Validate file size against maximum allowed size
        
        Args:
            content: File content as bytes
            max_size: Maximum allowed size in bytes
            
        Returns:
            bool: True if file size is within limits, False otherwise
        """
        return len(content) <= max_size and len(content) > 0 