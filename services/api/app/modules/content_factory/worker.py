"""Dedicated LOT 13 worker. Production runs this process separately from FastAPI."""
from __future__ import annotations
import os,time
from app.runtime import runtime

def main():
    actor=os.getenv('CONTENT_FACTORY_SYSTEM_ACCOUNT_ID')
    if not actor: raise RuntimeError('CONTENT_FACTORY_SYSTEM_ACCOUNT_ID is mandatory for the factory worker')
    poll=max(.5,float(os.getenv('CONTENT_FACTORY_POLL_SECONDS','2')))
    while True:
        queued=[r for r in runtime.content_factory_repository.list_runs(200) if r.state.value in {'queued','failed'} and r.attempt<r.max_attempts]
        if not queued: time.sleep(poll); continue
        for run in reversed(queued):
            try: runtime.content_factory.process(actor,run.id)
            except Exception: pass
if __name__=='__main__': main()
