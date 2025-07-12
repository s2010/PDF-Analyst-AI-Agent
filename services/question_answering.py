import logging
from typing import List, Dict

import openai
from fastapi import HTTPException

from core.config import settings

logger = logging.getLogger(__name__)


class QuestionAnsweringService:
    """Question answering service using OpenAI"""
    
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
    
    def generate_answer(self, question: str, context_chunks: List[Dict]) -> str:
        """
        Generate answer using OpenAI chat completion
        
        Args:
            question: User's question
            context_chunks: List of relevant chunks with metadata
            
        Returns:
            str: Generated answer
        """
        if not context_chunks:
            return "No relevant information found to answer your question."
        
        # Build context from chunks
        context_parts = []
        current_length = 0
        
        for chunk in context_chunks:
            chunk_text = f"[Page {chunk['metadata']['page_number']}]: {chunk['content']}"
            if current_length + len(chunk_text) > settings.MAX_CONTEXT_LENGTH:
                break
            context_parts.append(chunk_text)
            current_length += len(chunk_text)
        
        context = "\n\n".join(context_parts)
        
        system_prompt = """You are a helpful assistant that answers questions based on PDF documents. 
        Use only the provided context to answer questions. If the answer cannot be found in the context, 
        say so clearly. Always reference page numbers when providing answers."""
        
        user_prompt = f"""Context from PDF:
{context}

Question: {question}

Please provide a comprehensive answer based on the context above. Include relevant page numbers in your response."""
        
        try:
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1000,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            answer = response.choices[0].message.content.strip()
            logger.info(f"Generated answer for question: '{question[:50]}...'")
            return answer
        
        except openai.error.RateLimitError:
            logger.error("OpenAI rate limit exceeded for chat completion")
            raise HTTPException(
                status_code=429, 
                detail="Service temporarily unavailable"
            )
        except openai.error.AuthenticationError:
            logger.error("OpenAI authentication failed for chat completion")
            raise HTTPException(
                status_code=500, 
                detail="Service configuration error"
            )
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to generate answer"
            )
    
    def prepare_sources(self, context_chunks: List[Dict], max_content_length: int = 200) -> List[Dict]:
        """
        Prepare source information for response
        
        Args:
            context_chunks: List of relevant chunks with metadata
            max_content_length: Maximum length for content preview
            
        Returns:
            List[Dict]: Formatted source information
        """
        sources = []
        for chunk in context_chunks:
            content_preview = chunk["content"]
            if len(content_preview) > max_content_length:
                content_preview = content_preview[:max_content_length] + "..."
            
            sources.append({
                "content": content_preview,
                "page_number": chunk["metadata"]["page_number"],
                "filename": chunk["metadata"]["filename"],
                "similarity_score": round(chunk["similarity_score"], 4),
                "chunk_id": chunk["metadata"]["chunk_id"]
            })
        
        return sources 