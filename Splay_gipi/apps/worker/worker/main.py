from __future__ import annotations
import os
from redis import Redis
from rq import Worker, Queue, Connection

def main():
    url = os.getenv("REDIS_URL","redis://localhost:6379/0")
    redis = Redis.from_url(url)
    with Connection(redis):
        worker = Worker([Queue("scans")])
        worker.work(with_scheduler=False)

if __name__ == "__main__":
    main()
