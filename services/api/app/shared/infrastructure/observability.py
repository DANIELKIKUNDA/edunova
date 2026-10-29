from __future__ import annotations
import json, logging, time, uuid
from starlette.middleware.base import BaseHTTPMiddleware
from app.modules.operations.application.metrics import metrics

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({"ts":self.formatTime(record),"level":record.levelname,"logger":record.name,"message":record.getMessage()},separators=(",",":"),ensure_ascii=False)

def configure_logging():
    handler=logging.StreamHandler(); handler.setFormatter(JsonFormatter())
    root=logging.getLogger(); root.handlers=[handler]; root.setLevel(logging.INFO)

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id=request.headers.get('X-Request-ID') or uuid.uuid4().hex
        request.state.request_id=request_id; start=time.perf_counter()
        try: response=await call_next(request)
        except Exception:
            logging.getLogger('edunova.http').exception('request_failed request_id=%s path=%s',request_id,request.url.path); raise
        metrics.observe_http(request.method,request.url.path,response.status_code,time.perf_counter()-start)
        response.headers['X-Request-ID']=request_id
        logging.getLogger('edunova.http').info('request request_id=%s method=%s path=%s status=%s duration_ms=%s',request_id,request.method,request.url.path,response.status_code,round((time.perf_counter()-start)*1000))
        return response
