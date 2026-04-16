#!/bin/sh
# Railway deployment start script
# Handles PORT environment variable properly

export PORT=${PORT:-8000}

echo "Starting gunicorn on port 8000..."

exec gunicorn app.api.main:app \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120








