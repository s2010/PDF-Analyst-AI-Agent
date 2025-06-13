FROM python:3.10-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install system dependencies and security updates
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    g++ \
    curl \
    ca-certificates \
    && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with security flags
RUN pip install --no-cache-dir \
    --upgrade pip \
    --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

# Copy all application code including refactored modules
COPY main.py .
COPY core/ ./core/
COPY routers/ ./routers/
COPY services/ ./services/
COPY utils/ ./utils/
COPY models/ ./models/

# Create data directory and set permissions
RUN mkdir -p data logs \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Set environment variables for security
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Add labels for better maintainability
LABEL maintainer="PDF Analyst AI Agent"
LABEL version="1.0.0"
LABEL description="Secure PDF analysis service with AI-powered question answering"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use exec form for better signal handling
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"] 