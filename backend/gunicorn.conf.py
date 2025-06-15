"""
Gunicorn configuration file for production deployment.
"""
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Worker timeouts
timeout = 30
keepalive = 5
graceful_timeout = 30

# Logging
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()

# Process naming
proc_name = "gamechat-ai"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Environment variables
raw_env = [
    f"ENVIRONMENT={os.getenv('ENVIRONMENT', 'production')}",
    f"LOG_LEVEL={os.getenv('LOG_LEVEL', 'INFO')}",
]

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 50

# Graceful shutdown
graceful_timeout = 30

# Enable access log
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s %(p)s'

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")
