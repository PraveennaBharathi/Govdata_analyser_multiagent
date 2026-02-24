# 🚀 START THE BACKEND SERVER

## Quick Start (If dependencies are already installed)

```bash
cd /Users/praveennabharathi/Documents/Projects/backend
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## OR use the run script:

```bash
cd /Users/praveennabharathi/Documents/Projects/backend
python3 run.py
```

---

## If you need to install dependencies first:

### Option 1: Install all at once
```bash
cd /Users/praveennabharathi/Documents/Projects/backend
pip3 install fastapi uvicorn pandas sqlalchemy pydantic pydantic-settings python-dotenv matplotlib openpyxl langchain langchain-google-genai langchain-mistralai langgraph
```

### Option 2: Use the install script
```bash
cd /Users/praveennabharathi/Documents/Projects/backend
chmod +x install.sh
./install.sh
```

---

## Once Running:

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs  
- **Health**: http://localhost:8000/health

## Test Query:

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me employment trends from 2020 to 2024"}'
```

---

## Your API Keys are configured in `.env`:
✅ Gemini (Primary)
✅ Mistral (Fallback)
