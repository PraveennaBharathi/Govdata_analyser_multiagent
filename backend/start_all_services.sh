#!/bin/bash

# Startup script for all backend services
# This script starts Redis, Celery worker, and FastAPI server

echo "=========================================="
echo "Starting GovData Analytics Backend"
echo "=========================================="

# Check if Redis is running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis..."
    redis-server --daemonize yes
    sleep 2
else
    echo "✓ Redis already running"
fi

# Check Redis connection
if redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis connection successful"
else
    echo "✗ Redis connection failed"
    exit 1
fi

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A config.celery_config worker --loglevel=info --detach --logfile=logs/celery.log

sleep 3

# Check if Celery worker started
if pgrep -f "celery worker" > /dev/null; then
    echo "✓ Celery worker started"
else
    echo "✗ Celery worker failed to start"
    exit 1
fi

# Start FastAPI server
echo "Starting FastAPI server..."
echo "=========================================="
echo "Server will be available at:"
echo "  - API: http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo "  - WebSocket: ws://localhost:8000/ws/*"
echo "=========================================="
echo ""

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
