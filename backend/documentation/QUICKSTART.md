# Quick Start Guide

## Prerequisites
Make sure you have Python 3.9+ installed and the following packages:
```bash
pip install fastapi uvicorn pandas langchain langchain-google-genai langchain-mistralai sqlalchemy pydantic pydantic-settings python-dotenv matplotlib openpyxl langgraph
```

## Start the Server

### Option 1: Using the run script
```bash
cd backend
python3 run.py
```

### Option 2: Using uvicorn directly
```bash
cd backend
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Using the main.py
```bash
cd backend/api
python3 main.py
```

## Test the API

Once running, visit:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Test Query

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me employment trends from 2020 to 2024"}'
```

## Environment Variables

Make sure your `.env` file has:
```
GEMINI_API_KEY=your_key_here
MISTRAL_API_KEY=your_key_here
```

The system will use Gemini as primary, Mistral as fallback.
