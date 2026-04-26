# Gunicorn configuration for Leapcell deployment
# Fixes read-only filesystem issues by using /tmp for all runtime files

# Use /tmp for all gunicorn runtime files (read-only filesystem fix)
pidfile = "/tmp/gunicorn.pid"
worker_tmp_dir = "/tmp"

# Disable prometheus stats and control socket to avoid read-only filesystem issues
statsd_host = None

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Worker configuration
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 300
graceful_timeout = 60
