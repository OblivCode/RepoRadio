#!/bin/bash
# RepoRadio Startup Script for Linux/Mac
# This script activates the virtual environment and starts the Streamlit app

set -e  # Exit on error

echo "🎙️ Starting RepoRadio..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    
    echo "📦 Installing dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "✅ Activating virtual environment..."
    source venv/bin/activate
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found!"
    echo "💡 Copy .env.example to .env and configure your API keys"
    echo "   Example: cp .env.example .env"
    echo ""
fi

# Run Streamlit
echo "🚀 Launching RepoRadio on http://localhost:8501"
echo "   Press Ctrl+C to stop"
echo ""
streamlit run src/app.py
