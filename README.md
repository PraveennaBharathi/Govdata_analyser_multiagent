# GovData Analyser

A Singapore government data intelligence platform that answers natural-language questions about housing, labour, and live city conditions using a multi-agent AI pipeline backed by live data.gov.sg APIs.

---

## What it does

Type a question in plain English — *"Which HDB towns have risen the fastest since 2020?"* or *"How healthy is Singapore's labour market?"* — and the system:

1. Parses the intent with an LLM
2. Fetches live government datasets from data.gov.sg
3. Runs domain-specific analytics (HDB resale, MOM labour metrics, cross-domain correlation)
4. Streams results back with a conversational narrative, stat cards, charts, and a live city dashboard (PSI air quality + 2-hour weather)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Next.js Frontend                     │
│  QueryInput → AgentMonitor → ResultsView / LiveCityView  │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / polling
┌──────────────────────▼──────────────────────────────────┐
│                  FastAPI Backend                          │
│  POST /query/async → background task → GET /task/{id}    │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│            LangGraph 5-Node Pipeline                     │
│  parse_query → create_plan → extract_data                │
│             → analyze_data → generate_final_result       │
└────────┬──────────────────────────┬─────────────────────┘
         │                          │
┌────────▼─────────┐   ┌────────────▼───────────────────┐
│   LLM Service    │   │      Analytics Agents           │
│ Tier 1: Ollama   │   │  HDBAnalytics                   │
│  qwen2.5:14b     │   │  LabourAnalytics                │
│ Tier 2: Mistral  │   │  CrossDomainAnalytics           │
│  small/large/    │   └────────────┬───────────────────┘
│  magistral       │                │
│ Tier 3: Gemini   │   ┌────────────▼───────────────────┐
└──────────────────┘   │     Data Sources                │
                       │  data.gov.sg v1 API (HDB, MOM) │
                       │  NEA PSI + weather (no key)     │
                       │  SQLite query history           │
                       └────────────────────────────────┘
```

### LLM routing

| Mode | Model | Used for |
|------|-------|----------|
| Local | Ollama `qwen2.5:14b` | Unlimited; dev fallback |
| Routing | `mistral-small-latest` | Query parsing, fast tasks |
| Narrative | `mistral-large-latest` | Conversational summaries |
| Reasoning | `magistral-medium-latest` | Cross-domain analysis |
| Fallback | `gemini-flash-latest` | When Mistral quota exceeded |

---

## Project structure

```
Projects/
├── README.md
├── .env                        # Root env (NEXT_PUBLIC_API_URL)
├── .gitignore
├── docker-compose.yml
│
├── backend/
│   ├── api/
│   │   ├── main.py             # FastAPI app, all routes
│   │   ├── background_tasks.py # Async task queue + status store
│   │   └── websocket.py        # WebSocket endpoints (optional)
│   ├── agents/
│   │   ├── coordinator_agent.py # LangGraph graph builder & orchestrator
│   │   ├── extraction/
│   │   │   └── extraction_agent.py  # Calls data.gov.sg, routes by domain
│   │   └── analytics/
│   │       ├── analytics_agent.py   # Dispatches to domain-specific classes
│   │       ├── hdb_analytics.py     # HDB resale: trends, storey, PSM, momentum
│   │       ├── labour_analytics.py  # MOM: composite health score, 4 metrics
│   │       ├── crossdomain_analytics.py  # HDB × Labour Pearson correlation
│   │       ├── report_generator.py
│   │       └── statistical_methods.py
│   ├── services/
│   │   ├── datagov_client.py   # data.gov.sg v1 API client (1-hour cache)
│   │   ├── live_city_client.py # NEA PSI + weather (10-min cache)
│   │   └── llm_service.py      # 3-tier LLM dispatcher
│   ├── config/
│   │   ├── settings.py         # Pydantic settings (reads .env)
│   │   └── celery_config.py
│   ├── models/
│   │   └── database.py         # SQLAlchemy models (Query table)
│   ├── utils/
│   │   └── json_utils.py       # NaN / Inf sanitiser for JSON serialisation
│   ├── tasks/
│   │   └── query_tasks.py
│   ├── tests/
│   ├── data/                   # Static CSV / XLSX fallback data
│   ├── .env                    # Backend secrets (see below)
│   ├── .env.example
│   ├── requirements.txt
│   ├── Dockerfile
│   └── run.py
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx        # Main dashboard
│   │   │   ├── layout.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── QueryInput.tsx  # Natural language input + example chips
│   │   │   ├── AgentMonitor.tsx # Live pipeline step tracker
│   │   │   ├── ResultsView.tsx  # Stat cards, charts, tables
│   │   │   └── LiveCityView.tsx # PSI + weather dashboard
│   │   ├── lib/
│   │   │   ├── api.ts          # API client (submit, poll, history)
│   │   │   └── utils.ts
│   │   └── types/
│   │       └── index.ts        # All TypeScript interfaces
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   └── Dockerfile
│
└── docs/                       # Helper docs & API keys — gitignored
    ├── backend/
    └── frontend/
```

---

## Prerequisites

| Tool | Version | Required for |
|------|---------|-------------|
| Python | 3.11+ | Backend |
| Node.js | 18+ | Frontend |
| Ollama | any | Local LLM (optional but free) |
| Redis | 7+ | Background task queue (optional) |

API keys needed (at least one LLM key):

| Key | Where to get |
|-----|-------------|
| `DATAGOVSG_API_KEY` | https://guide.data.gov.sg/developers/api-overview |
| `MISTRAL_API_KEY` | https://console.mistral.ai |
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey |
| `OPENAI_API_KEY` | https://platform.openai.com (optional) |

---

## Local setup

### 1. Clone and configure

```bash
git clone <repo-url>
cd Projects
```

Create `backend/.env` (copy from the example):

```bash
cp backend/.env.example backend/.env
```

Fill in your keys:

```env
DATAGOVSG_API_KEY=your_key_here
MISTRAL_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here

DATABASE_URL=sqlite:///./govdata.db
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
TEMPERATURE=0.1
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Start the backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 4. (Optional) Ollama for free local LLM

```bash
ollama pull qwen2.5:14b
ollama serve
```

The LLM service automatically uses Ollama when Mistral/Gemini quotas are exhausted.

---

## Docker (full stack)

```bash
cp backend/.env.example backend/.env   # fill in your keys
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

---

## API reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/health` | Detailed service status |
| `POST` | `/query` | Synchronous query (waits for result) |
| `POST` | `/query/async` | Async query — returns `task_id` |
| `GET` | `/task/{task_id}` | Poll task status + result |
| `GET` | `/queries` | Last 50 query history |
| `GET` | `/queries/{id}` | Single query result |
| `GET` | `/live-city` | Live PSI air quality + weather |
| `WS` | `/ws/task/{task_id}` | Real-time task updates (WebSocket) |

**Example — submit and poll:**

```bash
# Submit
curl -X POST http://localhost:8000/query/async \
  -H "Content-Type: application/json" \
  -d '{"query": "Which HDB towns have the highest prices in 2025?"}'

# Poll (use task_id from above)
curl http://localhost:8000/task/<task_id>
```

---

## Live datasets

| Domain | Dataset | Source |
|--------|---------|--------|
| Housing | HDB Resale Flat Prices | data.gov.sg |
| Labour | Unemployment Rate (quarterly) | MOM via data.gov.sg |
| Labour | Quarterly Retrenchments | MOM via data.gov.sg |
| Labour | Recruitment Rate | MOM via data.gov.sg |
| Labour | Long-term Unemployment | MOM via data.gov.sg |
| Live city | PSI readings (5 regions) | NEA open API |
| Live city | 2-hour weather forecast (47 areas) | NEA open API |

All data.gov.sg datasets are fetched on demand and cached in-memory for 1 hour. NEA data is cached for 10 minutes.

---

## Key analytics

**HDB analytics** — storey band premium (Low/Mid/High), price-per-sqm by flat type, town momentum (2023–25 vs 2020–22 price acceleration), top-10 and bottom-5 town tables.

**Labour health score** — weighted composite (0–100) across unemployment rate (30%), retrenchments (25%), recruitment rate (25%), and long-term unemployment (20%). Normalised against absolute reference bounds so COVID-year scores are not artificially floored.

**Cross-domain** — Pearson correlation between annual HDB median prices and the labour health score (r ≈ −0.90 vs unemployment, r ≈ +0.48 vs composite score).

---

## Testing

```bash
cd backend
pytest tests/
```

---

## Environment variables — full reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DATAGOVSG_API_KEY` | — | data.gov.sg API key (required) |
| `MISTRAL_API_KEY` | — | Mistral API key |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `OPENAI_API_KEY` | — | OpenAI key (optional legacy) |
| `DATABASE_URL` | `sqlite:///./govdata.db` | SQLAlchemy connection string |
| `API_HOST` | `0.0.0.0` | Bind address |
| `API_PORT` | `8000` | Backend port |
| `DEBUG` | `true` | Enables FastAPI debug mode |
| `TEMPERATURE` | `0.1` | LLM sampling temperature |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama endpoint |
| `OLLAMA_MODEL` | `qwen2.5:14b` | Ollama model to use |
| `REDIS_HOST` | `localhost` | Redis host (if using Celery) |
| `REDIS_PORT` | `6379` | Redis port |
