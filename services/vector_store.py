import json
import logging
import pickle
from typing import List, Dict
from pathlib import Path

import numpy as np
import faiss
import openai
from fastapi import HTTPException

from core.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Vector database service using FAISS"""
    
    def __init__(self):
        self.index = None
        self.dimension = 1536  # OpenAI ada-002 embedding dimension
        self.chunks = []
        self.metadata = []
        self.document_metadata = {}
        
        # Configure OpenAI
        openai.api_key = settings.OPENAI_API_KEY
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Create embeddings using OpenAI API
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            np.ndarray: Array of embeddings
        """
        try:
            # Batch process to avoid rate limits
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = openai.Embedding.create(
                    model=settings.EMBEDDING_MODEL,
                    input=batch
                )
                batch_embeddings = [item['embedding'] for item in response['data']]
                all_embeddings.extend(batch_embeddings)
            
            logger.info(f"Created embeddings for {len(texts)} texts")
            return np.array(all_embeddings)
            
        except openai.error.RateLimitError:
            logger.error("OpenAI rate limit exceeded")
            raise HTTPException(
                status_code=429, 
                detail="Service temporarily unavailable due to rate limits"
            )
        except openai.error.AuthenticationError:
            logger.error("OpenAI authentication failed")
            raise HTTPException(
                status_code=500, 
                detail="Service configuration error"
            )
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to process document"
            )
    
    def add_documents(self, chunks: List[str], metadata: List[Dict]):
        """
        Add document chunks to vector database
        
        Args:
            chunks: List of text chunks
            metadata: List of metadata dictionaries
        """
        if not chunks:
            return
        
        # Check limits
        if len(self.chunks) + len(chunks) > settings.MAX_TOTAL_CHUNKS:
            raise HTTPException(
                status_code=413, 
                detail=f"Maximum number of chunks ({settings.MAX_TOTAL_CHUNKS}) exceeded"
            )
        
        # Create embeddings
        embeddings = self.create_embeddings(chunks)
        
        # Initialize index if needed
        if self.index is None:
            self.index = faiss.IndexFlatIP(self.dimension)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add to index
        self.index.add(embeddings)
        
        # Store chunks and metadata
        self.chunks.extend(chunks)
        self.metadata.extend(metadata)
        
        logger.info(f"Added {len(chunks)} chunks to vector database")
    
    def search(self, query: str, k: int = None) -> List[Dict]:
        """
        Search for similar chunks
        
        Args:
            query: Search query string
            k: Number of results to return
            
        Returns:
            List[Dict]: Search results with content and metadata
        """
        k = k or settings.MAX_RESULTS
        
        if self.index is None or self.index.ntotal == 0:
            return []
        
        if not query or len(query.strip()) == 0:
            return []
        
        # Create query embedding
        query_embedding = self.create_embeddings([query])
        faiss.normalize_L2(query_embedding)
        
        # Search with bounds checking
        search_k = min(k, self.index.ntotal, 20)
        scores, indices = self.index.search(query_embedding, search_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.chunks):
                results.append({
                    "content": self.chunks[idx],
                    "metadata": self.metadata[idx],
                    "similarity_score": float(score)
                })
        
        logger.info(f"Search returned {len(results)} results")
        return results
    
    def save(self, path: Path = None):
        """
        Save vector database to disk
        
        Args:
            path: Optional custom path
        """
        path = path or settings.VECTOR_DB_PATH
        
        try:
            path.mkdir(parents=True, exist_ok=True)
            
            if self.index is not None:
                faiss.write_index(self.index, str(path / "index.faiss"))
            
            with open(path / "chunks.pkl", "wb") as f:
                pickle.dump(self.chunks, f)
            
            with open(path / "metadata.pkl", "wb") as f:
                pickle.dump(self.metadata, f)
            
            # Save document metadata
            with open(settings.METADATA_PATH, "w") as f:
                json.dump(self.document_metadata, f, indent=2)
            
            logger.info(f"Vector database saved to {path}")
            
        except Exception as e:
            logger.error(f"Error saving vector database: {e}")
    
    def load(self, path: Path = None):
        """
        Load vector database from disk
        
        Args:
            path: Optional custom path
        """
        path = path or settings.VECTOR_DB_PATH
        
        try:
            if not path.exists():
                logger.info("No existing vector database found")
                return
            
            index_path = path / "index.faiss"
            if index_path.exists():
                self.index = faiss.read_index(str(index_path))
            
            chunks_path = path / "chunks.pkl"
            if chunks_path.exists():
                with open(chunks_path, "rb") as f:
                    self.chunks = pickle.load(f)
            
            metadata_path = path / "metadata.pkl"
            if metadata_path.exists():
                with open(metadata_path, "rb") as f:
                    self.metadata = pickle.load(f)
            
            # Load document metadata
            if settings.METADATA_PATH.exists():
                try:
                    with open(settings.METADATA_PATH, "r") as f:
                        self.document_metadata = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to load document metadata: {e}")
                    self.document_metadata = {}
            
            logger.info(f"Vector database loaded from {path}")
            
        except Exception as e:
            logger.error(f"Error loading vector database: {e}")
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the vector store
        
        Returns:
            Dict: Statistics including document and chunk counts
        """
        return {
            "total_documents": len(self.document_metadata),
            "total_chunks": len(self.chunks),
            "index_size": self.index.ntotal if self.index else 0,
            "documents": list(self.document_metadata.values())
        }
    
    def add_document_metadata(self, doc_id: str, metadata: Dict):
        """
        Add metadata for a processed document
        
        Args:
            doc_id: Document identifier
            metadata: Document metadata
        """
        self.document_metadata[doc_id] = metadata
        logger.info(f"Added metadata for document: {doc_id}") 