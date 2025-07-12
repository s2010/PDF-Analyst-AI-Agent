# PDF Document Processor

A FastAPI-based document processing service that extracts text from PDF files and enables semantic search capabilities.

## Features

- PDF text extraction and processing
- Semantic search with vector embeddings
- RESTful API with automatic documentation
- Rate limiting and security controls
- Persistent vector storage

## Quick Start

1. **Setup Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

2. **Run with Docker**
   ```bash
   docker-compose up --build
   ```

3. **Access API**
   - Service: http://localhost:8000
   - Documentation: http://localhost:8000/docs

## API Endpoints

- `POST /api/upload` - Upload PDF documents
- `POST /api/ask` - Query document content
- `GET /api/status` - System status
- `GET /health` - Health check

## Configuration

Configure via environment variables in `.env`:
- `OPENAI_API_KEY` - Required for embeddings
- `MAX_FILE_SIZE` - Maximum file size (default: 50MB)
- `MAX_PDF_PAGES` - Maximum pages per document (default: 500)

## License

MIT License 