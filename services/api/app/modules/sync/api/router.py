from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.modules.sync.domain.model import DeviceRegistration, SyncMutation, SyncOperation
from app.runtime import runtime
from app.shared.security.rate_limit import RateLimitExceeded

router = APIRouter()


class RegisterDeviceRequest(BaseModel):
    device_id: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=160)
    platform: str = Field(max_length=32)
    app_version: str = Field(min_length=1, max_length=40)


class MutationInput(BaseModel):
    mutation_id: str = Field(min_length=8, max_length=128)
    entity_type: str = Field(min_length=2, max_length=64)
    entity_id: str = Field(min_length=1, max_length=128)
    operation: SyncOperation = SyncOperation.UPSERT
    payload: dict = Field(default_factory=dict)
    base_version: int | None = Field(default=None, ge=0)
    client_modified_at: datetime


class PushRequest(BaseModel):
    device_id: str = Field(min_length=8, max_length=128)
    mutations: list[MutationInput] = Field(min_length=1, max_length=100)


class AckRequest(BaseModel):
    device_id: str = Field(min_length=8, max_length=128)
    cursor: int = Field(ge=0)


def _record(r):
    if r is None:
        return None
    return {
        "entity_type": r.entity_type, "entity_id": r.entity_id, "version": r.version,
        "payload": r.payload, "deleted": r.deleted, "updated_at": r.updated_at, "server_seq": r.server_seq,
    }


@router.post("/devices", status_code=201)
def register_device(req: RegisterDeviceRequest, auth: AuthContext = Depends(current_auth)) -> dict:
    try:
        runtime.sync.register_device(account_id=auth.account_id, registration=DeviceRegistration(**req.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    runtime.audit.write(actor_id=auth.account_id, action="sync.device.registered", entity_type="sync_device", entity_id=req.device_id, metadata={"platform": req.platform, "app_version": req.app_version})
    return {"registered": True, "device_id": req.device_id}


@router.post("/push")
def push(req: PushRequest, auth: AuthContext = Depends(current_auth)) -> dict:
    try:
        runtime.rate_limiter.check(key=f"sync-push:{auth.account_id}", limit=120, window_seconds=60)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail="sync_rate_limit") from exc
    mutations = tuple(SyncMutation(
        mutation_id=m.mutation_id, entity_type=m.entity_type, entity_id=m.entity_id,
        operation=m.operation, payload=m.payload, base_version=m.base_version,
        client_modified_at=m.client_modified_at,
    ) for m in req.mutations)
    try:
        outcomes = runtime.sync.push(account_id=auth.account_id, device_id=req.device_id, mutations=mutations)
    except ValueError as exc:
        code = str(exc)
        status = 403 if code in {"local_only_entity_cannot_sync", "server_authoritative_entity_cannot_push"} else 422
        raise HTTPException(status_code=status, detail=code) from exc
    conflicts = sum(1 for x in outcomes if x.disposition.value == "conflict")
    runtime.audit.write(actor_id=auth.account_id, action="sync.push", entity_type="sync_batch", metadata={"count": len(outcomes), "conflicts": conflicts})
    return {
        "outcomes": [
            {"mutation_id": x.mutation_id, "disposition": x.disposition.value, "reason": x.reason, "record": _record(x.record), "canonical": _record(x.canonical)}
            for x in outcomes
        ]
    }



@router.get("/bootstrap")
def bootstrap(device_id: str = Query(min_length=8, max_length=128), auth: AuthContext = Depends(current_auth)) -> dict:
    try:
        runtime.rate_limiter.check(key=f"sync-pull:{auth.account_id}", limit=240, window_seconds=60)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail="sync_rate_limit") from exc
    try:
        page = runtime.sync.bootstrap(account_id=auth.account_id, device_id=device_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"changes": [_record(x) for x in page.changes], "next_cursor": page.next_cursor, "has_more": False, "retained_floor": page.retained_floor, "reset_required": False}

@router.get("/pull")
def pull(device_id: str = Query(min_length=8, max_length=128), cursor: int = Query(default=0, ge=0), limit: int = Query(default=200, ge=1, le=500), auth: AuthContext = Depends(current_auth)) -> dict:
    try:
        runtime.rate_limiter.check(key=f"sync-pull:{auth.account_id}", limit=240, window_seconds=60)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail="sync_rate_limit") from exc
    try:
        page = runtime.sync.pull(account_id=auth.account_id, device_id=device_id, cursor=cursor, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "changes": [_record(x) for x in page.changes],
        "next_cursor": page.next_cursor,
        "has_more": page.has_more,
        "retained_floor": page.retained_floor,
        "reset_required": page.reset_required,
    }


@router.get("/devices")
def devices(auth: AuthContext = Depends(current_auth)) -> dict:
    rows = runtime.sync.list_devices(account_id=auth.account_id)
    return {"devices": [{
        "device_id": d.device_id, "name": d.name, "platform": d.platform, "app_version": d.app_version,
        "acked_cursor": d.acked_cursor, "created_at": d.created_at, "last_seen_at": d.last_seen_at,
        "last_sync_at": d.last_sync_at, "revoked_at": d.revoked_at, "active": d.active,
    } for d in rows]}


@router.delete("/devices/{device_id}")
def revoke_device(device_id: str, auth: AuthContext = Depends(current_auth)) -> dict:
    try:
        runtime.sync.revoke_device(account_id=auth.account_id, device_id=device_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    runtime.audit.write(actor_id=auth.account_id, action="sync.device.revoked", entity_type="sync_device", entity_id=device_id)
    return {"revoked": True, "device_id": device_id}


@router.post("/ack")
def acknowledge(req: AckRequest, auth: AuthContext = Depends(current_auth)) -> dict:
    try:
        cursor = runtime.sync.acknowledge(account_id=auth.account_id, device_id=req.device_id, cursor=req.cursor)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"acked_cursor": cursor}


@router.post("/maintenance/compact")
def compact(auth: AuthContext = Depends(current_auth)) -> dict:
    # This endpoint is authenticated and intentionally account-scoped. In production a scheduler
    # can invoke repository maintenance directly for all accounts.
    return runtime.sync.compact(account_id=auth.account_id)


@router.get("/policy")
def policy(auth: AuthContext = Depends(current_auth)) -> dict:
    from app.modules.sync.domain.model import SYNC_POLICIES
    return {k: v.policy.value for k, v in SYNC_POLICIES.items()}
