from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.modules.delivery.application.service import DeliveryError, RangeNotSatisfiable
from app.runtime import runtime
from app.shared.security.rate_limit import RateLimitExceeded

router = APIRouter()


def _account_id(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        return "anonymous"
    try:
        token = authorization.split(" ", 1)[1].strip()
        return runtime.authenticator.authenticate(token).account_id
    except Exception as exc:
        raise HTTPException(status_code=401, detail="delivery_auth_invalid") from exc


def _map_error(exc: DeliveryError):
    code = str(exc)
    if code in {"delivery_token_invalid_or_expired", "delivery_premium_required"}:
        return 403
    if code in {"delivery_resource_not_found", "delivery_course_not_published"}:
        return 404
    if code == "delivery_range_not_satisfiable":
        return 416
    return 422


@router.get("/resources/{resource_id}/grant")
def grant(resource_id: str, request: Request, token: str = Query(min_length=10), purpose: str = Query(default="stream"), authorization: str | None = Header(default=None)):
    account_id = _account_id(authorization)
    try:
        runtime.rate_limiter.check(key=f"delivery-grant:{account_id}", limit=120, window_seconds=60)
        g = runtime.delivery.grant(
            account_id=account_id, resource_id=resource_id, token=token,
            public_base_url=str(request.base_url).rstrip('/'), ttl_seconds=300, purpose=purpose,
        )
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail="delivery_rate_limited") from exc
    except DeliveryError as exc:
        raise HTTPException(status_code=_map_error(exc), detail=str(exc)) from exc
    return {
        "resource_id": g.resource_id, "url": g.url, "expires_at": g.expires_at,
        "size_bytes": g.size_bytes, "checksum_sha256": g.checksum_sha256, "etag": g.etag,
        "content_type": g.content_type, "supports_range": g.supports_range, "requires_app_auth": g.requires_app_auth,
    }


@router.get("/resources/{resource_id}/content")
def content(resource_id: str, token: str = Query(min_length=10), range_header: str | None = Header(default=None, alias="Range"), authorization: str | None = Header(default=None)):
    try:
        resource, stat, part = runtime.delivery.prepare_proxy(
            account_id=_account_id(authorization), resource_id=resource_id, token=token, range_header=range_header,
        )
    except DeliveryError as exc:
        headers = {"Content-Range": f"bytes */{exc.total}"} if isinstance(exc, RangeNotSatisfiable) else None
        raise HTTPException(status_code=_map_error(exc), detail=str(exc), headers=headers) from exc
    stream = runtime.delivery.storage.open_range(resource.storage_locator, start=part.start, end=part.end)
    status = 206 if range_header else 200
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(part.length),
        "ETag": stat.etag or (resource.checksum_sha256 or ""),
        "Cache-Control": "private, no-store",
    }
    if status == 206:
        headers["Content-Range"] = f"bytes {part.start}-{part.end}/{part.total}"
    return StreamingResponse(stream, status_code=status, media_type=resource.mime_type or stat.content_type or "application/octet-stream", headers=headers)
