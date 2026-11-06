from __future__ import annotations

import os
import signal
import threading
import time
from uuid import uuid4

from app.runtime import runtime


def run() -> None:
    worker_id=os.getenv('INGESTION_WORKER_ID',f'worker-{uuid4().hex[:12]}')
    poll=max(0.2,float(os.getenv('INGESTION_WORKER_POLL_SECONDS','1.0')))
    stop=threading.Event()
    def _stop(*_): stop.set()
    signal.signal(signal.SIGTERM,_stop); signal.signal(signal.SIGINT,_stop)
    last_recovery=0.0
    while not stop.is_set():
        now_mono=time.monotonic()
        if now_mono-last_recovery>=60:
            runtime.ingestion.recover_expired_leases_internal(); last_recovery=now_mono
        job=runtime.ingestion.claim_job(worker_id=worker_id)
        if job is None:
            stop.wait(poll); continue
        heartbeat_stop=threading.Event()
        def beat():
            interval=max(5,runtime.ingestion.lease_seconds//3)
            while not heartbeat_stop.wait(interval):
                if not runtime.ingestion.heartbeat(worker_id=worker_id,job_id=job.id): return
        thread=threading.Thread(target=beat,daemon=True); thread.start()
        try:
            runtime.ingestion.process_job(worker_id=worker_id,job_id=job.id)
        except Exception:
            # process_job records retry/dead-letter state before re-raising.
            pass
        finally:
            heartbeat_stop.set(); thread.join(timeout=2)


if __name__=='__main__': run()
