import os
from pathlib import Path
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # External API Configuration
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", description="OpenAI chat model")
    EMBEDDING_MODEL: str = Field(default="text-embedding-ada-002", description="OpenAI embedding model")
    
    # Processing Configuration
    CHUNK_SIZE: int = Field(default=1000, description="Text chunk size")
    CHUNK_OVERLAP: int = Field(default=200, description="Chunk overlap")
    MAX_RESULTS: int = Field(default=5, description="Default search results")
    MAX_CONTEXT_LENGTH: int = Field(default=4000, description="Maximum context length")
    
    # Resource Limits
    MAX_FILE_SIZE: int = Field(default=52428800, description="Maximum file size (50MB)")
    MAX_QUESTION_LENGTH: int = Field(default=1000, description="Maximum question length")
    MAX_PDF_PAGES: int = Field(default=500, description="Maximum PDF pages")
    MAX_CHUNKS_PER_DOCUMENT: int = Field(default=1000, description="Maximum chunks per document")
    MAX_TOTAL_CHUNKS: int = Field(default=10000, description="Maximum total chunks")
    
    # Security & Rate Limiting
    RATE_LIMIT_REQUESTS: str = Field(default="100/hour", description="Rate limit")
    ALLOWED_HOSTS: Union[str, List[str]] = Field(default="localhost,127.0.0.1,0.0.0.0", description="Allowed hosts")
    CORS_ORIGINS: Union[str, List[str]] = Field(default="http://localhost:3000", description="CORS origins")
    
    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment type")
    DATA_DIR: Path = Field(default=Path("data"), description="Data directory")
    
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
        """Initialize data directories"""
        self.DATA_DIR.mkdir(exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings() 