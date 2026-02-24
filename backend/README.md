# GovData Analytics Backend

Agentic Policy Data Analytics Platform Backend built with FastAPI, LangGraph, and multi-LLM support.

## Features

- **Multi-Agent System**: Coordinator Agent for query processing and analysis planning
- **LLM Integration**: OpenAI primary with Gemini fallback
- **Database**: SQLite for query storage and results
- **RESTful API**: FastAPI with async support
- **Query Processing**: Natural language to structured analysis plans

## Tech Stack

- **Framework**: FastAPI
- **Agentic Framework**: LangGraph
- **LLM Providers**: OpenAI + Google Gemini
- **Database**: SQLite with SQLAlchemy
- **Data Processing**: Pandas, NumPy
- **Testing**: pytest

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run the application:
```bash
cd api
python main.py
```

Or using uvicorn:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Health Check
- `GET /` - Basic health check
- `GET /health` - Detailed service status

### Query Processing
- `POST /query` - Process user query through agents
  ```json
  {
    "query": "Show me employment trends from 2020 to 2024"
  }
  ```
- `GET /queries` - Get all processed queries
- `GET /queries/{query_id}` - Get specific query result

## Agent Workflow

1. **Query Parsing**: LLM parses natural language into structured format
2. **Plan Creation**: Creates analysis plan based on parsed query
3. **Analysis Execution**: Executes analysis and generates insights

## Example Query Response

```json
{
  "query_id": 1,
  "status": "success",
  "parsed_query": {
    "dataset": "employment",
    "year_range": "2020-2024",
    "analysis": "trend"
  },
  "analysis_plan": [
    "Extract employment data for 2020-2024",
    "Perform trend analysis",
    "Generate insights and visualizations",
    "Create structured report"
  ],
  "result": {
    "dataset": "employment",
    "year_range": "2020-2024",
    "analysis_type": "trend",
    "status": "completed",
    "insights": [...],
    "data_points": [...]
  },
  "workflow_steps": ["parse_query", "create_plan", "execute_analysis"]
}
```

## Testing

```bash
pytest tests/
```

## Architecture

```
backend/
├── agents/           # Agent implementations
├── api/             # FastAPI endpoints
├── config/          # Configuration settings
├── models/          # Database models
├── services/        # LLM and external services
└── tests/           # Test suite
```
