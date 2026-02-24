#!/bin/bash
# Quick install script for backend dependencies

echo "📦 Installing backend dependencies..."

pip3 install fastapi uvicorn[standard] pandas sqlalchemy pydantic pydantic-settings python-dotenv matplotlib openpyxl

echo "🧠 Installing LLM packages..."
pip3 install langchain langchain-google-genai langchain-mistralai langchain-openai

echo "🔧 Installing LangGraph..."
pip3 install langgraph

echo "✅ Installation complete!"
echo ""
echo "To start the server, run:"
echo "  cd backend"
echo "  python3 run.py"
