from __future__ import annotations
import os
import sys
from pathlib import Path
from redis import Redis
from rq import Queue

def _redis() -> Redis:
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(url)

def _process_inline(scan_id: str) -> None:
    # Fallback for local dev without Redis/Docker.
    repo_root = Path(__file__).resolve().parents[3]
    worker_root = repo_root / "apps" / "worker"
    matching_root = repo_root / "packages" / "matching_core"
    sys.path.insert(0, str(worker_root))
    sys.path.insert(0, str(matching_root))
    from worker.jobs import process_scan
    process_scan(scan_id)

def enqueue_scan(scan_id: str) -> None:
    mode = os.getenv("QUEUE_MODE", "redis").lower()
    if mode == "inline":
        _process_inline(scan_id)
        return
    try:
        q = Queue("scans", connection=_redis())
        q.enqueue("worker.jobs.process_scan", scan_id, job_timeout=60)
    except Exception:
        _process_inline(scan_id)
