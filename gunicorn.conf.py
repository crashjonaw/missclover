"""Gunicorn config for MISS CLOVER.

Run with:  gunicorn -c gunicorn.conf.py app:app
Or just:   gunicorn app:app  (uses this file automatically if in the same dir)

Tuned for ~500–1000 concurrent users on a modest VPS (2–4 CPU cores, 2–4 GB RAM).
"""
import multiprocessing
import os

# ── Bind ──────────────────────────────────────────────────────────────────────
bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:5002")

# ── Workers ───────────────────────────────────────────────────────────────────
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# ── Threads per worker ────────────────────────────────────────────────────────
threads = int(os.environ.get("GUNICORN_THREADS", 4))

# ── Worker class ──────────────────────────────────────────────────────────────
# gthread = threaded workers (best for I/O-bound Flask apps with SQLite)
worker_class = "gthread"

# ── Timeouts ──────────────────────────────────────────────────────────────────
timeout = 120
graceful_timeout = 30
keepalive = 5

# ── Memory leak protection ────────────────────────────────────────────────────
max_requests = 1000
max_requests_jitter = 100

# ── Preload ───────────────────────────────────────────────────────────────────
preload_app = False

# ── Logging ───────────────────────────────────────────────────────────────────
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOGLEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" %(D)sμs'

# ── Process naming ────────────────────────────────────────────────────────────
proc_name = "missclover"


def on_starting(server):
    print("=" * 55)
    print("  MISS CLOVER — Gunicorn")
    print(f"  Bind:    {bind}")
    print(f"  Workers: {workers} × {threads} threads = {workers * threads} concurrent")
    print("  Press Ctrl+C to stop")
    print("=" * 55)
