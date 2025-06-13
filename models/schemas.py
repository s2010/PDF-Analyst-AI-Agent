from typing import List, Dict, Optional
from pydantic import BaseModel, Field, validator

from core.config import settings


class QuestionRequest(BaseModel):
    """Request model for asking questions about PDF content"""
    question: str = Field(..., min_length=1, max_length=settings.MAX_QUESTION_LENGTH)
    max_results: Optional[int] = Field(default=settings.MAX_RESULTS, ge=1, le=20)
    
    @validator('question')
    def sanitize_question(cls, v):
        """Remove potential harmful characters and limit length"""
        sanitized = ''.join(char for char in v if char.isprintable())
        return sanitized.strip()


class SourceInfo(BaseModel):
    """Information about a source chunk"""
    content: str = Field(..., description="Preview of the source content")
    page_number: int = Field(..., description="Page number in the original document")
    filename: str = Field(..., description="Original filename")
    similarity_score: float = Field(..., description="Similarity score for the match")
    chunk_id: str = Field(..., description="Unique identifier for the chunk")


class AnswerResponse(BaseModel):
    """Response model for question answering"""
    answer: str = Field(..., description="Generated answer to the question")
    sources: List[SourceInfo] = Field(..., description="List of source chunks used")
    query: str = Field(..., description="Original question")
    processing_time: float = Field(..., description="Time taken to process the request")


class UploadResponse(BaseModel):
    """Response model for PDF upload"""
    message: str = Field(..., description="Status message")
    document_id: str = Field(..., description="Unique identifier for the uploaded document")
    pages_processed: int = Field(..., description="Number of pages processed")
    processing_time: float = Field(..., description="Time taken to process the upload")


class DocumentInfo(BaseModel):
    """Information about a processed document"""
    filename: str = Field(..., description="Original filename")
    pages_count: int = Field(..., description="Number of pages in the document")
    chunks_count: int = Field(..., description="Number of text chunks created")
    upload_time: str = Field(..., description="Upload timestamp")
    file_hash: str = Field(..., description="SHA-256 hash of the file")
    file_size: int = Field(..., description="File size in bytes")


class StatusResponse(BaseModel):
    """Response model for system status"""
    status: str = Field(..., description="System status")
    total_documents: int = Field(..., description="Total number of processed documents")
    total_chunks: int = Field(..., description="Total number of text chunks")
    uptime: str = Field(..., description="System uptime")
    version: str = Field(..., description="Application version")


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="Current timestamp")


class ChunkMetadata(BaseModel):
    """Metadata for a text chunk"""
    document_id: str = Field(..., description="Document identifier")
    filename: str = Field(..., description="Original filename")
    page_number: int = Field(..., description="Page number")
    chunk_index: int = Field(..., description="Index of chunk within page")
    chunk_id: str = Field(..., description="Unique chunk identifier")
    file_hash: str = Field(..., description="File hash for integrity")


class PageContent(BaseModel):
    """Content extracted from a PDF page"""
    page_number: int = Field(..., description="Page number")
    content: str = Field(..., description="Extracted text content")
    char_count: int = Field(..., description="Character count")


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details") 