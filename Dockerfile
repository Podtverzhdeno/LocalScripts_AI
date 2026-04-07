FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    lua5.4 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Initialize RAG database
RUN python -m rag.cli init || echo "RAG init failed, will retry at runtime"

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/sessions || exit 1

# Run FastAPI server
CMD ["python", "api/server.py"]
