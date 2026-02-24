"""
WebSocket Endpoints for Real-Time Updates
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import logging
import json
import asyncio
from celery.result import AsyncResult
from config.celery_config import celery_app

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        """Accept WebSocket connection and add to task subscribers"""
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
        logger.info(f"WebSocket connected for task {task_id}")
    
    def disconnect(self, websocket: WebSocket, task_id: str):
        """Remove WebSocket connection"""
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        logger.info(f"WebSocket disconnected for task {task_id}")
    
    async def send_update(self, task_id: str, message: dict):
        """Send update to all subscribers of a task"""
        if task_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    disconnected.add(connection)
            
            # Remove disconnected clients
            for connection in disconnected:
                self.active_connections[task_id].discard(connection)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for task_connections in self.active_connections.values():
            for connection in task_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting: {e}")

manager = ConnectionManager()

async def websocket_task_updates(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time task updates
    
    Usage:
        ws://localhost:8000/ws/task/{task_id}
    
    Messages sent:
        - {"type": "status", "state": "PENDING|PROCESSING|SUCCESS|FAILURE", "progress": 0-100}
        - {"type": "progress", "current": 40, "total": 100, "status": "Extracting data..."}
        - {"type": "result", "data": {...}}
        - {"type": "error", "message": "..."}
    """
    await manager.connect(websocket, task_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "task_id": task_id,
            "message": "Connected to task updates"
        })
        
        # Monitor task progress
        task_result = AsyncResult(task_id, app=celery_app)
        last_state = None
        
        while True:
            try:
                # Get current task state
                state = task_result.state
                info = task_result.info
                
                # Send update if state changed
                if state != last_state:
                    message = {
                        "type": "status",
                        "state": state,
                        "task_id": task_id
                    }
                    
                    if state == 'PENDING':
                        message["status"] = "Task is waiting to be processed"
                        message["progress"] = 0
                    
                    elif state == 'PROCESSING':
                        if isinstance(info, dict):
                            message["status"] = info.get('status', 'Processing...')
                            message["progress"] = info.get('current', 0)
                            message["total"] = info.get('total', 100)
                    
                    elif state == 'SUCCESS':
                        message["status"] = "Task completed successfully"
                        message["progress"] = 100
                        message["result"] = info
                        await websocket.send_json(message)
                        break  # Task complete, close connection
                    
                    elif state == 'FAILURE':
                        message["status"] = "Task failed"
                        message["error"] = str(info)
                        await websocket.send_json(message)
                        break  # Task failed, close connection
                    
                    else:
                        message["status"] = f"Task state: {state}"
                    
                    await websocket.send_json(message)
                    last_state = state
                
                # Check for client messages (e.g., cancel request)
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
                    client_message = json.loads(data)
                    
                    if client_message.get('action') == 'cancel':
                        task_result.revoke(terminate=True)
                        await websocket.send_json({
                            "type": "cancelled",
                            "message": "Task cancellation requested"
                        })
                        break
                
                except asyncio.TimeoutError:
                    pass  # No message from client, continue monitoring
                
                # Small delay to avoid overwhelming the client
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error monitoring task: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error monitoring task: {str(e)}"
                })
                break
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from task {task_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    
    finally:
        manager.disconnect(websocket, task_id)


async def websocket_query_stream(websocket: WebSocket, query_id: int):
    """
    WebSocket endpoint for streaming query results
    
    Usage:
        ws://localhost:8000/ws/query/{query_id}
    
    Streams analysis results as they become available
    """
    await websocket.accept()
    
    try:
        await websocket.send_json({
            "type": "connected",
            "query_id": query_id,
            "message": "Connected to query stream"
        })
        
        # Stream updates about query processing
        # This can be extended to stream partial results
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Echo back for now (can be extended)
            await websocket.send_json({
                "type": "echo",
                "data": message
            })
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from query {query_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


async def websocket_system_status(websocket: WebSocket):
    """
    WebSocket endpoint for system status updates
    
    Usage:
        ws://localhost:8000/ws/status
    
    Broadcasts system health and metrics
    """
    await websocket.accept()
    
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to system status"
        })
        
        while True:
            # Send system status every 5 seconds
            await asyncio.sleep(5)
            
            # Get Celery worker stats
            try:
                stats = celery_app.control.inspect().stats()
                active_tasks = celery_app.control.inspect().active()
                
                await websocket.send_json({
                    "type": "system_status",
                    "timestamp": asyncio.get_event_loop().time(),
                    "workers": stats or {},
                    "active_tasks": active_tasks or {},
                    "status": "healthy" if stats else "no_workers"
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "system_status",
                    "status": "error",
                    "error": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info("Client disconnected from system status")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
