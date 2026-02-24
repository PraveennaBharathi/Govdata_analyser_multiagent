"""
Celery Tasks for Background Query Processing
"""
import asyncio
import logging
from typing import Dict, Any
from config.celery_config import celery_app
from agents.coordinator_agent import CoordinatorAgent
from models.database import SessionLocal, Query
from datetime import datetime

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='tasks.query_tasks.process_query_task')
def process_query_task(self, query_id: int, query_text: str) -> Dict[str, Any]:
    """
    Background task for processing user queries
    
    Args:
        self: Celery task instance
        query_id: Database ID of the query
        query_text: User's query text
    
    Returns:
        Dict containing task result
    """
    logger.info(f"Starting background task for query_id={query_id}")
    
    # Update task state to PROCESSING
    self.update_state(
        state='PROCESSING',
        meta={
            'current': 0,
            'total': 100,
            'status': 'Initializing query processing...'
        }
    )
    
    try:
        # Initialize coordinator agent
        coordinator = CoordinatorAgent()
        
        # Update progress: Parsing query
        self.update_state(
            state='PROCESSING',
            meta={
                'current': 20,
                'total': 100,
                'status': 'Parsing query...'
            }
        )
        
        # Process query asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Update progress: Extracting data
        self.update_state(
            state='PROCESSING',
            meta={
                'current': 40,
                'total': 100,
                'status': 'Extracting data from sources...'
            }
        )
        
        result = loop.run_until_complete(coordinator.process_query(query_text))
        loop.close()
        
        # Update progress: Analyzing data
        self.update_state(
            state='PROCESSING',
            meta={
                'current': 70,
                'total': 100,
                'status': 'Performing statistical analysis...'
            }
        )
        
        # Update database with result
        db = SessionLocal()
        try:
            query_record = db.query(Query).filter(Query.id == query_id).first()
            if query_record:
                query_record.status = result.get('status', 'completed')
                query_record.result = result
                query_record.parsed_query = result.get('parsed_query')
                db.commit()
                logger.info(f"Query {query_id} completed successfully")
        finally:
            db.close()
        
        # Update progress: Complete
        self.update_state(
            state='PROCESSING',
            meta={
                'current': 100,
                'total': 100,
                'status': 'Analysis complete!'
            }
        )
        
        return {
            'status': 'success',
            'query_id': query_id,
            'result': result
        }
        
    except Exception as e:
        logger.error(f"Task failed for query_id={query_id}: {e}")
        
        # Update database with error
        db = SessionLocal()
        try:
            query_record = db.query(Query).filter(Query.id == query_id).first()
            if query_record:
                query_record.status = 'failed'
                query_record.result = {'error': str(e)}
                db.commit()
        finally:
            db.close()
        
        # Update task state to FAILURE
        self.update_state(
            state='FAILURE',
            meta={
                'current': 0,
                'total': 100,
                'status': f'Task failed: {str(e)}'
            }
        )
        
        raise


@celery_app.task(name='tasks.query_tasks.cleanup_old_tasks')
def cleanup_old_tasks():
    """
    Periodic task to clean up old completed tasks
    """
    logger.info("Running cleanup of old tasks")
    # Implementation for cleanup logic
    return {'status': 'cleanup_complete'}
