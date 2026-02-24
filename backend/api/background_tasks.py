"""
Background Tasks using FastAPI BackgroundTasks (No Redis/Celery required)
"""
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from models.database import SessionLocal, Query
from agents.coordinator_agent import CoordinatorAgent

logger = logging.getLogger(__name__)

# In-memory task storage (for demo purposes)
task_storage: Dict[str, Dict[str, Any]] = {}

async def process_query_background(task_id: str, query_id: int, query_text: str):
    """
    Background task for processing queries without Celery
    """
    logger.info(f"Starting background task {task_id} for query_id={query_id}")
    
    # Update task status
    task_storage[task_id] = {
        "state": "PROCESSING",
        "progress": 0,
        "status": "Initializing...",
        "query_id": query_id
    }
    
    try:
        coordinator = CoordinatorAgent()
        
        # Update progress: Parsing
        task_storage[task_id].update({
            "progress": 20,
            "status": "Parsing query..."
        })
        await asyncio.sleep(0.5)
        
        # Update progress: Extracting
        task_storage[task_id].update({
            "progress": 40,
            "status": "Extracting data from sources..."
        })
        await asyncio.sleep(0.5)
        
        # Process query
        result = await coordinator.process_query(query_text)
        
        # Update progress: Analyzing
        task_storage[task_id].update({
            "progress": 70,
            "status": "Performing statistical analysis..."
        })
        await asyncio.sleep(0.5)
        
        # Update database
        db = SessionLocal()
        try:
            query_record = db.query(Query).filter(Query.id == query_id).first()
            if query_record:
                query_record.status = result.get('status', 'completed')
                query_record.result = result
                query_record.parsed_query = result.get('parsed_query')
                query_record.completed_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()
        
        # Update task: Complete
        task_storage[task_id].update({
            "state": "SUCCESS",
            "progress": 100,
            "status": "Analysis complete!",
            "result": result
        })
        
        logger.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        
        # Update database with error
        db = SessionLocal()
        try:
            query_record = db.query(Query).filter(Query.id == query_id).first()
            if query_record:
                query_record.status = 'failed'
                query_record.result = {'error': str(e)}
                query_record.completed_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()
        
        # Update task: Failed
        task_storage[task_id].update({
            "state": "FAILURE",
            "progress": 0,
            "status": f"Task failed: {str(e)}",
            "error": str(e)
        })

def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get status of a background task"""
    if task_id not in task_storage:
        return {
            "task_id": task_id,
            "state": "PENDING",
            "status": "Task not found or not started"
        }
    
    return {
        "task_id": task_id,
        **task_storage[task_id]
    }
