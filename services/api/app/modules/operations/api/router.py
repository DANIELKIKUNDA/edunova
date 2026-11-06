from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse
from app.modules.operations.application.metrics import metrics
from app.runtime import runtime
router=APIRouter()
@router.get('/live')
def live(): return runtime.operations.liveness()
@router.get('/ready')
def ready(response:Response):
    ok,payload=runtime.operations.readiness()
    if not ok: response.status_code=503
    return payload

@router.get('/metrics',response_class=PlainTextResponse)
def operational_metrics(): return metrics.render_prometheus()
