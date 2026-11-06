from __future__ import annotations
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Callable

@dataclass(frozen=True, slots=True)
class ProbeResult:
    name: str
    ok: bool
    latency_ms: int
    detail: str = ""

class OperationalHealthService:
    def __init__(self, probes: dict[str, Callable[[], None]], *, version: str):
        self.probes, self.version = probes, version

    def liveness(self) -> dict:
        return {"status":"alive","service":"edunova-api","version":self.version,"time":datetime.now(UTC).isoformat()}

    def readiness(self) -> tuple[bool, dict]:
        import time
        results=[]
        for name, probe in self.probes.items():
            start=time.perf_counter()
            try:
                probe(); ok=True; detail="ok"
            except Exception as exc:
                ok=False; detail=type(exc).__name__
            results.append(ProbeResult(name,ok,round((time.perf_counter()-start)*1000),detail))
        ready=all(x.ok for x in results)
        return ready,{"status":"ready" if ready else "not_ready","version":self.version,"checks":[{"name":x.name,"ok":x.ok,"latency_ms":x.latency_ms,"detail":x.detail} for x in results]}
