from typing import List, Dict, Optional
from pydantic import BaseModel, Field, validator

from core.config import settings


class QuestionRequest(BaseModel):
    """Request model for document queries"""
    question: str = Field(..., min_length=1, max_length=settings.MAX_QUESTION_LENGTH)
    max_results: Optional[int] = Field(default=settings.MAX_RESULTS, ge=1, le=20)
    
    @validator('question')
    def sanitize_question(cls, v):
        """Remove harmful characters and limit length"""
        sanitized = ''.join(char for char in v if char.isprintable())
        return sanitized.strip()


class SourceInfo(BaseModel):
    """Source chunk information"""
    content: str = Field(..., description="Content preview")
    page_number: int = Field(..., description="Page number in document")
    filename: str = Field(..., description="Original filename")
    similarity_score: float = Field(..., description="Similarity score")
    chunk_id: str = Field(..., description="Unique chunk identifier")


class AnswerResponse(BaseModel):
    """Question answering response"""
    answer: str = Field(..., description="Generated answer")
    sources: List[SourceInfo] = Field(..., description="Source chunks")
    query: str = Field(..., description="Original question")
    processing_time: float = Field(..., description="Processing time")


class UploadResponse(BaseModel):
    """PDF upload response"""
    message: str = Field(..., description="Status message")
    document_id: str = Field(..., description="Document identifier")
    pages_processed: int = Field(..., description="Pages processed")
    processing_time: float = Field(..., description="Processing time")


class DocumentInfo(BaseModel):
    """Document information"""
    filename: str = Field(..., description="Original filename")
    pages_count: int = Field(..., description="Page count")
    chunks_count: int = Field(..., description="Chunk count")
    upload_time: str = Field(..., description="Upload timestamp")
    file_hash: str = Field(..., description="File hash")
    file_size: int = Field(..., description="File size in bytes")


class StatusResponse(BaseModel):
    """System status response"""
    status: str = Field(..., description="System status")
    total_documents: int = Field(..., description="Total documents")
    total_chunks: int = Field(..., description="Total chunks")
    uptime: str = Field(..., description="System uptime")
    version: str = Field(..., description="Application version")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="Current timestamp")


class ChunkMetadata(BaseModel):
    """Text chunk metadata"""
    document_id: str = Field(..., description="Document identifier")
    filename: str = Field(..., description="Original filename")
    page_number: int = Field(..., description="Page number")
    chunk_index: int = Field(..., description="Chunk index")
    chunk_id: str = Field(..., description="Unique chunk identifier")
    file_hash: str = Field(..., description="File hash")


class PageContent(BaseModel):
    """PDF page content"""
    page_number: int = Field(..., description="Page number")
    content: str = Field(..., description="Text content")
    char_count: int = Field(..., description="Character count")


class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details") 