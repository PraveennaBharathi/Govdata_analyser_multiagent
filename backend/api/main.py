from fastapi import FastAPI, HTTPException, Depends, WebSocket, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
import uuid
from datetime import datetime

from models.database import get_db, init_db, Query
from agents.coordinator_agent import CoordinatorAgent
from api.background_tasks import process_query_background, get_task_status

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional: Try to import WebSocket (graceful fallback)
try:
    from api.websocket import websocket_task_updates, websocket_query_stream, websocket_system_status
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    logger.warning("WebSocket features not available")

# Initialize FastAPI app
app = FastAPI(
    title="GovData Analytics API",
    description="Agentic Policy Data Analytics Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize coordinator agent
coordinator = CoordinatorAgent()

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    logger.info("Database initialized")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "message": "GovData Analytics API is running"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "running",
            "database": "connected",
            "llm_service": "initialized"
        }
    }

@app.post("/query")
async def process_query(
    request: Dict[str, str],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Process user query through the agent system (synchronous)
    
    Expected request format:
    {
        "query": "Show me employment trends from 2020 to 2024"
    }
    """
    try:
        user_query = request.get("query", "")
        if not user_query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        logger.info(f"Processing query: {user_query}")
        
        # Save query to database
        db_query = Query(
            user_query=user_query,
            parsed_query={},
            status="processing"
        )
        db.add(db_query)
        db.commit()
        db.refresh(db_query)
        
        # Process through coordinator agent
        result = await coordinator.process_query(user_query)
        
        # Update database with results
        db_query.parsed_query = result.get("parsed_query", {})
        db_query.status = result.get("status", "error")
        db_query.result = result
        db_query.completed_at = datetime.utcnow()
        db.commit()
        
        return {
            "query_id": db_query.id,
            "status": result.get("status"),
            "parsed_query": result.get("parsed_query"),
            "analysis_plan": result.get("analysis_plan"),
            "result": result.get("result"),
            "workflow_steps": result.get("workflow_steps")
        }
        
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/async")
async def process_query_async(
    request: Dict[str, str],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Process user query asynchronously using FastAPI background task
    
    Expected request format:
    {
        "query": "Show me employment trends from 2020 to 2024"
    }
    
    Returns task_id for tracking progress
    """
    try:
        user_query = request.get("query", "")
        if not user_query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        logger.info(f"Queuing async query: {user_query}")
        
        # Save query to database
        db_query = Query(
            user_query=user_query,
            parsed_query={},
            status="queued"
        )
        db.add(db_query)
        db.commit()
        db.refresh(db_query)
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Queue background task
        background_tasks.add_task(
            process_query_background,
            task_id,
            db_query.id,
            user_query
        )
        
        return {
            "query_id": db_query.id,
            "task_id": task_id,
            "status": "queued",
            "message": "Query queued for processing",
            "status_url": f"http://localhost:8000/task/{task_id}",
            "websocket_url": f"ws://localhost:8000/ws/task/{task_id}" if WEBSOCKET_AVAILABLE else None
        }
        
    except Exception as e:
        logger.error(f"Query queueing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/task/{task_id}")
async def get_task_status_endpoint(task_id: str) -> Dict[str, Any]:
    """
    Get status of a background task
    """
    try:
        status = get_task_status(task_id)
        return status
        
    except Exception as e:
        logger.error(f"Task status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/queries")
async def get_queries(db: Session = Depends(get_db)):
    """Get all processed queries"""
    queries = db.query(Query).order_by(Query.created_at.desc()).limit(50).all()
    
    return [
        {
            "id": q.id,
            "user_query": q.user_query,
            "status": q.status,
            "created_at": q.created_at.isoformat(),
            "completed_at": q.completed_at.isoformat() if q.completed_at else None,
            "parsed_query": q.parsed_query,
            "result": q.result
        }
        for q in queries
    ]

@app.get("/queries/{query_id}")
async def get_query(query_id: int, db: Session = Depends(get_db)):
    """Get specific query by ID"""
    query = db.query(Query).filter(Query.id == query_id).first()
    
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    
    return {
        "id": query.id,
        "user_query": query.user_query,
        "status": query.status,
        "created_at": query.created_at.isoformat(),
        "completed_at": query.completed_at.isoformat() if query.completed_at else None,
        "parsed_query": query.parsed_query,
        "analysis_plan": query.result.get("analysis_plan", []) if query.result else [],
        "result": query.result
    }

@app.get("/live-city")
async def get_live_city() -> Dict[str, Any]:
    """Real-time PSI air quality + 2-hour weather forecast (no API key required)."""
    try:
        from services.live_city_client import get_live_city_data
        return get_live_city_data()
    except Exception as e:
        logger.error(f"Live city data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket Endpoints (if available)
if WEBSOCKET_AVAILABLE:
    @app.websocket("/ws/task/{task_id}")
    async def websocket_task_endpoint(websocket: WebSocket, task_id: str):
        """WebSocket endpoint for real-time task updates"""
        await websocket_task_updates(websocket, task_id)
    
    @app.websocket("/ws/query/{query_id}")
    async def websocket_query_endpoint(websocket: WebSocket, query_id: int):
        """WebSocket endpoint for streaming query results"""
        await websocket_query_stream(websocket, query_id)
    
    @app.websocket("/ws/status")
    async def websocket_status_endpoint(websocket: WebSocket):
        """WebSocket endpoint for system status updates"""
        await websocket_system_status(websocket)
else:
    logger.info("WebSocket endpoints not registered (dependencies not available)")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
