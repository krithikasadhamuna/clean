#!/bin/bash
# CodeGrey AI SOC Platform - Local Development Environment

echo "CodeGrey AI SOC Platform - Development Environment"
echo "=================================================="
echo

# Set development environment
export SOC_ENV=development
export PYTHONPATH="$(pwd)"

echo "Starting development server on localhost:8080..."
echo
echo "Development Features:"
echo "  - Debug logging enabled"
echo "  - CORS fully open"
echo "  - No authentication required"
echo "  - Hot reload enabled"
echo "  - API docs: http://localhost:8080/docs"
echo

# Install development dependencies
echo "Installing development dependencies..."
pip3 install --user psutil aiohttp fastapi uvicorn pydantic langchain langchain-openai openai

echo
echo "🚀 Starting development server..."
echo

# Start development server
python3 start_dev_server.py

