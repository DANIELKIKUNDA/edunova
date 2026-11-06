from __future__ import annotations
import json, logging, re, time, uuid
from starlette.middleware.base import BaseHTTPMiddleware
from app.modules.operations.application.metrics import metrics

_SECRET = re.compile(r"(?i)(authorization|cookie|password|token|secret|api[-_]?key)=([^\s,;]+)")


def _safe(value: object, *, limit: int = 2048) -> str:
    """Return a bounded, single-line and secret-redacted log value."""
    text = str(value).replace("\r", "\\r").replace("\n", "\\n")
    text = _SECRET.sub(r"\1=[REDACTED]", text)
    return text[:limit]


class JsonFormatter(logging.Formatter):
    _standard = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime", "event"}
    _sensitive_key = re.compile(r"(?i)(authorization|cookie|password|token|secret|api[-_]?key)")

    def format(self, record):
        payload = {
            "ts": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "event": _safe(getattr(record, "event", record.msg if isinstance(record.msg, str) else "log"), limit=512),
            "message": _safe(record.getMessage()),
        }
        for key, value in record.__dict__.items():
            if key in self._standard or key.startswith("_") or value is None:
                continue
            payload[key] = "[REDACTED]" if self._sensitive_key.search(key) else value if isinstance(value, (bool, int, float)) else _safe(value, limit=512)
        if record.exc_info:
            payload["exception"] = _safe(self.formatException(record.exc_info))
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)

def configure_logging():
    handler=logging.StreamHandler(); handler.setFormatter(JsonFormatter())
    root=logging.getLogger(); root.handlers=[handler]; root.setLevel(logging.INFO)

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        supplied=request.headers.get('X-Request-ID','')
        request_id=supplied if re.fullmatch(r'[A-Za-z0-9._-]{8,128}',supplied) else uuid.uuid4().hex
        request.state.request_id=request_id; start=time.perf_counter()
        logger=logging.getLogger('edunova.http')
        try: response=await call_next(request)
        except Exception:
            duration_ms=round((time.perf_counter()-start)*1000,2)
            logger.exception('request_failed',extra={'event':'http.request.failed','request_id':request_id,'method':request.method,'path':request.url.path,'duration_ms':duration_ms}); raise
        elapsed=time.perf_counter()-start
        metrics.observe_http(request.method,request.url.path,response.status_code,elapsed)
        response.headers['X-Request-ID']=request_id
        logger.info('request_completed',extra={'event':'http.request.completed','request_id':request_id,'method':request.method,'path':request.url.path,'status':response.status_code,'duration_ms':round(elapsed*1000,2)})
        return response
