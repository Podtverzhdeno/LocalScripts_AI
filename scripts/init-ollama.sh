#!/bin/bash
# Auto-pull Ollama model on first startup

MODEL="${OLLAMA_MODEL:-qwen2.5-coder:7b-instruct-q4_K_M}"

echo "Checking if model $MODEL is available..."

# Check if model exists
if ollama list | grep -q "$MODEL"; then
    echo "✓ Model $MODEL already exists"
else
    echo "Downloading model $MODEL (this may take a few minutes, ~4GB)..."
    ollama pull "$MODEL"
    echo "✓ Model $MODEL downloaded successfully"
fi

echo "Ollama is ready!"
