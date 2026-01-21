#!/bin/bash

# STL Weight Calculator - Quick Start Script
# This script sets up and runs the application locally

echo "=================================="
echo "STL Weight Calculator - Setup"
echo "=================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install requirements
echo "📥 Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Run the app
echo "🚀 Starting Streamlit app..."
echo ""
echo "=================================="
echo "The app will open in your browser"
echo "Press Ctrl+C to stop the server"
echo "=================================="
echo ""

streamlit run app.py
