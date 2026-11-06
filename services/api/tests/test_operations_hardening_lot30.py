from datetime import UTC, datetime
import pytest
from app.shared.security.rate_limit import RedisRateLimiter, RateLimitExceeded
from app.modules.operations.application.metrics import OperationalMetrics

class Pipe:
    def __init__(self,r): self.r=r; self.key=None
    def incr(self,k): self.key=k; return self
    def ttl(self,k): return self
    def execute(self): self.r.values[self.key]=self.r.values.get(self.key,0)+1; return self.r.values[self.key], self.r.ttls.get(self.key,-1)
class Redis:
    def __init__(self): self.values={}; self.ttls={}
    def pipeline(self): return Pipe(self)
    def expire(self,k,s): self.ttls[k]=s

def test_redis_rate_limit_is_shared_across_instances():
    r=Redis(); a=RedisRateLimiter(r); b=RedisRateLimiter(r)
    a.check(key='login:x',limit=2,window_seconds=60); b.check(key='login:x',limit=2,window_seconds=60)
    with pytest.raises(RateLimitExceeded): a.check(key='login:x',limit=2,window_seconds=60)
    assert r.ttls['edunova:ratelimit:login:x']==60

def test_metrics_are_prometheus_parseable_contract():
    m=OperationalMetrics(); m.observe_http('GET','/health',200,.125); out=m.render_prometheus()
    assert 'edunova_http_requests_total{method="GET",route="/health",status="200"} 1' in out
    assert 'edunova_http_request_duration_seconds_count{method="GET",route="/health"} 1' in out
