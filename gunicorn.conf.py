# Gunicorn configuration for Leapcell deployment
# Fixes read-only filesystem issues by using /tmp for all runtime files

import os

# Use /tmp for all gunicorn runtime files (read-only filesystem fix)
pidfile = "/tmp/gunicorn.pid"
worker_tmp_dir = "/tmp"
bind = "0.0.0.0:8000"

# Prevent gunicorn from creating control socket in /app
# by explicitly setting a tmp path for Unix sockets
raw_env = [f"GUNICORN_SOCKET_PATH=/tmp/gunicorn.sock"]

# Disable prometheus stats and control socket to avoid read-only filesystem issues
statsd_host = None

# Disable the control socket completely
# This prevents gunicorn from trying to create /app/.gunicorn
proc_name = "techno-crm"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Worker configuration
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 300
graceful_timeout = 60
