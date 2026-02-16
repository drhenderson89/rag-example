#!/bin/bash

echo "================================"
echo "RAG Django App - Quick Start"
echo "================================"
echo ""

echo "Starting Docker containers..."
echo "(First run will download the Ollama model - may take 5-10 minutes)"
docker-compose up --build

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Access the application at: http://localhost:8000"
echo ""
echo "To run in background:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop:"
echo "  docker-compose down"
echo ""
