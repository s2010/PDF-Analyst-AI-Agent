import os
from pathlib import Path
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings for validation and environment variable parsing"""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key for embeddings and chat completion")
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", description="OpenAI chat model")
    EMBEDDING_MODEL: str = Field(default="text-embedding-ada-002", description="OpenAI embedding model")
    
    # Text Processing Configuration
    CHUNK_SIZE: int = Field(default=1000, description="Text chunk size for processing")
    CHUNK_OVERLAP: int = Field(default=200, description="Overlap between chunks")
    MAX_RESULTS: int = Field(default=5, description="Default number of search results")
    MAX_CONTEXT_LENGTH: int = Field(default=4000, description="Maximum context length for Q&A")
    
    # Security Configuration
    MAX_FILE_SIZE: int = Field(default=52428800, description="Maximum file size in bytes (50MB)")
    MAX_QUESTION_LENGTH: int = Field(default=1000, description="Maximum question length")
    MAX_PDF_PAGES: int = Field(default=500, description="Maximum PDF pages to process")
    MAX_CHUNKS_PER_DOCUMENT: int = Field(default=1000, description="Maximum chunks per document")
    MAX_TOTAL_CHUNKS: int = Field(default=10000, description="Maximum total chunks in system")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: str = Field(default="100/hour", description="Rate limit configuration")
    
    # Network Security
    ALLOWED_HOSTS: Union[str, List[str]] = Field(
        default="localhost,127.0.0.1,0.0.0.0", 
        description="Allowed host headers"
    )
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default="http://localhost:3000", 
        description="CORS allowed origins"
    )
    
    # Environment Configuration
    ENVIRONMENT: str = Field(default="development", description="Environment type")
    
    # Data Storage Paths
    DATA_DIR: Path = Field(default=Path("data"), description="Data directory path")
    
    @field_validator('ALLOWED_HOSTS', mode='before')
    @classmethod
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v
    
    @field_validator('CORS_ORIGINS', mode='before')  
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v
    
    @property
    def VECTOR_DB_PATH(self) -> Path:
        """Vector database storage path"""
        return self.DATA_DIR / "vector_db"
    
    @property
    def METADATA_PATH(self) -> Path:
        """Document metadata storage path"""
        return self.DATA_DIR / "metadata.json"
    
    def model_post_init(self, __context) -> None:
        """Initialize after model creation"""
        # Ensure data directory exists
        self.DATA_DIR.mkdir(exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings() 