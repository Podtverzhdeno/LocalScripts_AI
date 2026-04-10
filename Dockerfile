FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    lua5.4 \
    curl \
    sqlite3 \
    libsqlite3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download embedding model (optional, speeds up first run)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" || echo "Model download failed, will retry at runtime"

# Copy application code
COPY . .

# Create workspace directory
RUN mkdir -p /app/workspace

# Initialize RAG database (optional, can be done at runtime)
# Commented out to speed up build - will init on first run if RAG_ENABLED=true
# RUN python -m rag.cli init || echo "RAG init failed, will retry at runtime"

# Expose FastAPI port
EXPOSE 8000

# Health check with longer start period for RAG initialization
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/api/sessions || exit 1

# Run FastAPI server on 0.0.0.0 to accept external connections
CMD ["python", "api/server.py", "--host", "0.0.0.0"]

