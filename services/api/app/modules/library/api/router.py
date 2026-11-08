from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response

from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.runtime import runtime

router = APIRouter()


def _optional_account_id(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        return "anonymous"
    token = authorization.split(" ", 1)[1].strip()
    try:
        return runtime.authenticator.authenticate(token).account_id
    except Exception:
        return "anonymous"


def _course(c):
    return {"id": c.id, "faculty_domain": c.faculty_domain, "program": c.program, "level": c.level, "semester": c.semester, "title": c.title, "slug": c.slug, "description": c.description, "premium_required": c.premium_required, "active_version_id": c.active_version_id, "updated_at": c.updated_at}


@router.get("/catalog")
def catalog(
    response: Response, faculty_domain: str | None = None, program: str | None = None,
    level: str | None = None, semester: str | None = None, q: str | None = Query(default=None, max_length=120),
    cursor: str | None = Query(default=None, max_length=64), limit: int = Query(default=100, ge=1, le=200),
    if_none_match: str | None = Header(default=None, alias="If-None-Match"),
):
    try:
        page = runtime.library.catalog_page(
            faculty_domain=faculty_domain, program=program, level=level, semester=semester, query=q, cursor=cursor, limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    response.headers["ETag"] = page.etag
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    if if_none_match == page.etag:
        response.status_code = 304
        return None
    return {"courses": [_course(c) for c in page.courses], "next_cursor": page.next_cursor, "etag": page.etag}


@router.get("/courses/{course_id}")
def course(course_id: str) -> dict:
    try:
        c = runtime.library.get_course(course_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _course(c)


@router.get("/courses/{course_id}/manifest")
def manifest(course_id: str, authorization: str | None = Header(default=None)) -> dict:
    try:
        data = runtime.library.manifest(account_id=_optional_account_id(authorization), course_id=course_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    c = data["course"]; v = data["version"]
    return {
        "course": _course(c),
        "version": {"id": v.id, "label": v.label, "academic_year": v.academic_year, "source_fingerprint": v.source_fingerprint, "changelog": v.changelog, "published_at": v.published_at},
        "premium": data["premium"],
        "resources": [
            {"id": r.id, "kind": r.kind.value, "title": r.title, "mime_type": r.mime_type, "size_bytes": r.size_bytes, "checksum_sha256": r.checksum_sha256, "premium_required": r.premium_required, "offline_allowed": r.offline_allowed, "access": r.access, "delivery_token": r.delivery_token}
            for r in data["resources"]
        ],
    }
