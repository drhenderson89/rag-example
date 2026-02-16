#!/bin/bash

# Start Ollama service in the background
ollama serve &

# Wait for Ollama to be ready
echo "Waiting for Ollama service to start..."
sleep 5

# Check if model exists, if not pull it
echo "Checking if llama3.2 model exists..."
if ! ollama list | grep -q llama3.2; then
    echo "Model not found. Pulling llama3.2 (this may take several minutes)..."
    ollama pull llama3.2
    echo "Model downloaded successfully!"
else
    echo "Model already exists, skipping download."
fi

# Keep the container running by waiting on the background process
wait
