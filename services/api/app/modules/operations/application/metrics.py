from __future__ import annotations
from collections import defaultdict
from threading import Lock
import time

class OperationalMetrics:
    def __init__(self):
        self._lock=Lock(); self._counters=defaultdict(int); self._latency=defaultdict(lambda:[0.0,0])
    def observe_http(self, method:str, path:str, status:int, duration_seconds:float):
        route=(path if path in {'/health','/v1/operations/live','/v1/operations/ready','/v1/operations/metrics'} else 'other')
        with self._lock:
            self._counters[(method,route,status)]+=1; x=self._latency[(method,route)]; x[0]+=duration_seconds; x[1]+=1
    def render_prometheus(self)->str:
        lines=['# HELP edunova_http_requests_total HTTP requests','# TYPE edunova_http_requests_total counter']
        with self._lock:
            for (m,p,s),v in sorted(self._counters.items()): lines.append(f'edunova_http_requests_total{{method="{m}",route="{p}",status="{s}"}} {v}')
            lines += ['# HELP edunova_http_request_duration_seconds_sum HTTP request duration','# TYPE edunova_http_request_duration_seconds_sum counter']
            for (m,p),(total,count) in sorted(self._latency.items()):
                lines.append(f'edunova_http_request_duration_seconds_sum{{method="{m}",route="{p}"}} {total:.6f}')
                lines.append(f'edunova_http_request_duration_seconds_count{{method="{m}",route="{p}"}} {count}')
        return '\n'.join(lines)+'\n'
metrics=OperationalMetrics()
