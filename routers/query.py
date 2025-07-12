import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import settings
from models.schemas import (
    QuestionRequest, 
    AnswerResponse, 
    StatusResponse, 
    HealthResponse
)
from services.vector_store import VectorStoreService
from services.question_answering import QuestionAnsweringService

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def get_vector_store(request: Request) -> VectorStoreService:
    """Get vector store service from app state"""
    return request.app.state.vector_store


@router.post("/ask", response_model=AnswerResponse)
@limiter.limit(settings.RATE_LIMIT_REQUESTS)
async def ask_question(
    request: Request,
    question_request: QuestionRequest,
    vector_store: VectorStoreService = Depends(get_vector_store)
):
    """
    Query documents with natural language questions
    
    Args:
        request: FastAPI request object
        question_request: Question and parameters
        vector_store: Vector store service
        
    Returns:
        AnswerResponse: Generated answer with sources
    """
    start_time = datetime.now()
    
    try:
        # Search for relevant content
        relevant_chunks = vector_store.search(
            question_request.question, 
            k=question_request.max_results
        )
        
        if not relevant_chunks:
            return AnswerResponse(
                answer="No relevant information found. Please upload PDF documents first.",
                sources=[],
                query=question_request.question,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
        
        # Generate answer
        qa_service = QuestionAnsweringService()
        answer = qa_service.generate_answer(question_request.question, relevant_chunks)
        sources = qa_service.prepare_sources(relevant_chunks)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            f"Question answered in {processing_time:.2f}s: "
            f"'{question_request.question[:50]}...' -> {len(relevant_chunks)} sources"
        )
        
        return AnswerResponse(
            answer=answer,
            sources=sources,
            query=question_request.question,
            processing_time=processing_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error processing your question"
        )


@router.get("/status", response_model=StatusResponse)
async def get_status(
    vector_store: VectorStoreService = Depends(get_vector_store)
):
    """
    Get system status and statistics
    
    Args:
        vector_store: Vector store service
        
    Returns:
        StatusResponse: System status information
    """
    try:
        stats = vector_store.get_stats()
        
        return StatusResponse(
            status="healthy",
            total_documents=stats["total_documents"],
            total_chunks=stats["total_chunks"],
            uptime=datetime.now().isoformat(),
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving system status"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring
    
    Returns:
        HealthResponse: Health status
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    ) 