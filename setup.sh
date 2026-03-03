#!/bin/bash
# Decision Engine Setup Script
# Sets up Python environment and dependencies

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Setting up Decision Engine..."

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.11+ required. Found: $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/vector_store
mkdir -p output

# Copy environment template if .env doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "⚠️  Created .env - please add your API keys"
    fi
fi

echo "✅ Setup complete!"
echo ""
echo "To start the backend:"
echo "  source .venv/bin/activate"
echo "  python backend/main.py"
echo ""
echo "To use LMStudio (local LLM):"
echo "  1. Download LMStudio from https://lmstudio.ai"
echo "  2. Start LMStudio and load a model"
echo "  3. The backend will auto-detect it"
echo ""
echo "To use Gemini (cloud LLM):"
echo "  1. Get API key from https://aistudio.google.com/apikey"
echo "  2. Add GEMINI_API_KEY to .env"
