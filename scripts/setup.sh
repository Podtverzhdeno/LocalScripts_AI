#!/bin/bash
set -e

echo "🚀 Starting LocalScript for MTS True Tech Hack 2026..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Start services
echo "📦 Starting services (this may take a few minutes on first run)..."
docker-compose up -d

# Wait for Ollama to be healthy
echo ""
echo "⏳ Waiting for Ollama to start..."
timeout=60
elapsed=0
while ! docker exec localscript-ollama curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    if [ $elapsed -ge $timeout ]; then
        echo "❌ Timeout waiting for Ollama"
        exit 1
    fi
    sleep 2
    elapsed=$((elapsed + 2))
    echo -n "."
done
echo ""

# Pull model
echo ""
echo "📥 Pulling qwen2.5-coder:7b model (this may take 5-10 minutes on first run)..."
docker exec localscript-ollama ollama pull qwen2.5-coder:7b

# Wait for LocalScript to be healthy
echo ""
echo "⏳ Waiting for LocalScript API to start..."
timeout=30
elapsed=0
while ! curl -s http://localhost:8000/api/sessions > /dev/null 2>&1; do
    if [ $elapsed -ge $timeout ]; then
        echo "❌ Timeout waiting for LocalScript API"
        exit 1
    fi
    sleep 2
    elapsed=$((elapsed + 2))
    echo -n "."
done
echo ""

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Web UI:  http://localhost:8000"
echo "📡 API:     http://localhost:8000/docs"
echo "🤖 Ollama:  http://localhost:11434"
echo ""
echo "📊 View logs:    docker-compose logs -f"
echo "🛑 Stop:         docker-compose down"
echo "🗑️  Clean all:    docker-compose down -v"
echo ""
