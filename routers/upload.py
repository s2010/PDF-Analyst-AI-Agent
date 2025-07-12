import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import settings
from models.schemas import UploadResponse
from services.pdf_processor import PDFProcessor
from services.vector_store import VectorStoreService
from utils.file_utils import SecurityUtils, FileUtils

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def get_vector_store(request: Request) -> VectorStoreService:
    """Get vector store service from app state"""
    return request.app.state.vector_store


@router.post("/upload", response_model=UploadResponse)
@limiter.limit(settings.RATE_LIMIT_REQUESTS)
async def upload_pdf(
    request: Request,
    file: UploadFile = File(...),
    vector_store: VectorStoreService = Depends(get_vector_store)
):
    """
    Upload and process PDF documents
    
    Args:
        request: FastAPI request object
        file: PDF file upload
        vector_store: Vector store service
        
    Returns:
        UploadResponse: Processing results
    """
    start_time = datetime.now()
    
    # Validate file type
    if not SecurityUtils.validate_pdf_file(file):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Only PDF files are allowed"
        )
    
    # Read and validate file content
    file_content = await file.read()
    
    if not FileUtils.validate_file_size(file_content, settings.MAX_FILE_SIZE):
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        else:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {FileUtils.format_file_size(settings.MAX_FILE_SIZE)}"
            )
    
    # Generate document metadata
    doc_id = str(uuid.uuid4())
    safe_filename = SecurityUtils.sanitize_filename(file.filename)
    file_hash = SecurityUtils.calculate_file_hash(file_content)
    upload_path = settings.DATA_DIR / f"{doc_id}.pdf"
    
    try:
        # Save file temporarily
        with open(upload_path, "wb") as buffer:
            buffer.write(file_content)
        
        logger.info(f"Processing PDF: {safe_filename} -> {doc_id}")
        
        # Process PDF
        pdf_processor = PDFProcessor()
        chunks, partial_metadata = pdf_processor.process_pdf(str(upload_path))
        
        # Complete metadata
        metadata = []
        for i, partial_meta in enumerate(partial_metadata):
            complete_metadata = {
                "document_id": doc_id,
                "filename": safe_filename,
                "page_number": partial_meta["page_number"],
                "chunk_index": partial_meta["chunk_index"],
                "chunk_id": f"{doc_id}_page_{partial_meta['page_number']}_chunk_{partial_meta['chunk_index']}",
                "file_hash": file_hash
            }
            metadata.append(complete_metadata)
        
        # Store in vector database
        vector_store.add_documents(chunks, metadata)
        vector_store.save()
        
        # Calculate processing stats
        pages_processed = len(set(meta["page_number"] for meta in metadata))
        
        # Store document metadata
        document_metadata = {
            "filename": safe_filename,
            "pages_count": pages_processed,
            "chunks_count": len(chunks),
            "upload_time": datetime.now().isoformat(),
            "file_hash": file_hash,
            "file_size": len(file_content)
        }
        
        vector_store.add_document_metadata(doc_id, document_metadata)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            f"Document processed: {doc_id}, "
            f"{pages_processed} pages, {len(chunks)} chunks, "
            f"{processing_time:.2f}s"
        )
        
        return UploadResponse(
            message="PDF uploaded and processed successfully",
            document_id=doc_id,
            pages_processed=pages_processed,
            processing_time=processing_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error processing PDF file"
        )
    finally:
        # Clean up temporary file
        if upload_path.exists():
            try:
                upload_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary file: {e}") 