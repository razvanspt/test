#!/bin/bash
# Quick start script for CS2 Highlight Generator

echo "========================================="
echo "CS2 Highlight Generator - Quick Start"
echo "========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.11+ from https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python 3 detected: $(python3 --version)"
echo ""

# Check if requirements are installed
echo "📦 Checking dependencies..."
cd backend

if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "⚠️  Dependencies not installed. Installing now..."
    pip3 install -r requirements.txt
    echo ""
fi

echo "✅ Dependencies OK"
echo ""

# Start the server
echo "🚀 Starting backend server..."
echo ""
echo "Backend will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/api/docs"
echo ""
echo "To use the app:"
echo "1. Open frontend/index.html in your browser"
echo "2. Upload a .dem file"
echo "3. Wait for analysis"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "========================================="
echo ""

# Run the server
python3 main.py
