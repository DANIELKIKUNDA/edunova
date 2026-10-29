from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.modules.identity.application.auth_context import AuthContext
from app.modules.identity.application.service import RegisterInput
from app.runtime import runtime
from app.modules.commerce.domain.access_policy import AccessPolicy
from app.shared.security.rate_limit import RateLimitExceeded

router = APIRouter()


class RegisterRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=256)
    email: str | None = None
    phone_number: str | None = None
    device_name: str | None = Field(default=None, max_length=160)


class LoginRequest(BaseModel):
    login: str
    password: str
    device_name: str | None = None
    mfa_code: str | None = Field(default=None, min_length=6, max_length=6)


class RefreshRequest(BaseModel):
    refresh_token: str
    device_name: str | None = None


class LogoutRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=256)
    new_password: str = Field(min_length=8, max_length=256)


class RecoveryRequest(BaseModel):
    login: str = Field(min_length=3, max_length=320)


class RecoveryConfirmRequest(BaseModel):
    challenge_id: str
    code: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8, max_length=256)


class TokenResponse(BaseModel):
    account_id: str
    display_name: str
    access_token: str
    refresh_token: str
    expires_in_seconds: int


def current_auth(authorization: str | None = Header(default=None)) -> AuthContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing_bearer_token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        return runtime.authenticator.authenticate(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="invalid_or_expired_token") from exc


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(req: RegisterRequest, request: Request) -> TokenResponse:
    try:
        runtime.rate_limiter.check(key=f"register:{request.client.host if request.client else 'unknown'}", limit=8, window_seconds=3600)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail="too_many_attempts") from exc
    if not req.email and not req.phone_number:
        raise HTTPException(status_code=422, detail="email_or_phone_required")
    try:
        account, tokens = runtime.identity.register(RegisterInput(**req.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=409 if str(exc) == "login_already_exists" else 422, detail=str(exc)) from exc
    wallet = runtime.ai_wallets.get(account.id)
    if wallet.balance == 0:
        wallet.set_cycle_allowance(AccessPolicy().free_ai_trial_credits, datetime.now(UTC))
        runtime.ai_wallets.save(wallet)
    runtime.audit.write(actor_id=account.id, action="identity.register", entity_type="account", entity_id=account.id)
    return TokenResponse(account_id=account.id, display_name=account.display_name, **tokens.__dict__)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, request: Request) -> TokenResponse:
    key = f"login:{request.client.host if request.client else 'unknown'}:{req.login.strip().lower()}"
    try:
        runtime.rate_limiter.check(key=key, limit=8, window_seconds=900)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail="too_many_attempts") from exc
    login_data=req.model_dump(exclude={'mfa_code'})
    # MFA is checked before a persistent device session is issued. Keep the same
    # credential error for unknown/bad-password accounts to avoid enumeration.
    candidate=runtime.accounts.find_by_login(req.login)
    if not candidate or not runtime.password_hasher.verify(candidate.password_hash,req.password):
        raise HTTPException(status_code=401, detail='invalid_credentials')
    if runtime.trust_governance.mfa_enabled(candidate.id):
        if not req.mfa_code:
            raise HTTPException(status_code=401, detail='mfa_required')
        if not runtime.trust_governance.verify_mfa(candidate.id,req.mfa_code):
            raise HTTPException(status_code=401, detail='invalid_mfa_code')
    try:
        account, tokens = runtime.identity.login(**login_data)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    runtime.audit.write(actor_id=account.id, action="identity.login", entity_type="account", entity_id=account.id)
    return TokenResponse(account_id=account.id, display_name=account.display_name, **tokens.__dict__)


@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest) -> TokenResponse:
    try:
        tokens = runtime.identity.refresh(req.refresh_token, req.device_name)
        payload = runtime.token_issuer.decode_access(tokens.access_token)
        account = runtime.accounts.get(str(payload["sub"]))
        assert account is not None
    except Exception as exc:
        raise HTTPException(status_code=401, detail="invalid_refresh_token") from exc
    return TokenResponse(account_id=account.id, display_name=account.display_name, **tokens.__dict__)


@router.post("/logout", status_code=204)
def logout(req: LogoutRequest) -> None:
    runtime.identity.logout(req.refresh_token)


@router.get("/me")
def me(auth: AuthContext = Depends(current_auth)) -> dict:
    account = runtime.accounts.get(auth.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="account_not_found")
    return {
        "id": account.id,
        "display_name": account.display_name,
        "email": account.email,
        "phone_number": account.phone_number,
        "state": account.state.value,
    }


@router.get("/sessions")
def sessions(auth: AuthContext = Depends(current_auth)) -> list[dict]:
    return [
        {
            "id": s.id,
            "device_name": s.device_name,
            "created_at": s.created_at,
            "expires_at": s.expires_at,
            "active": s.active,
        }
        for s in runtime.identity.list_sessions(auth.account_id)
    ]


@router.delete("/sessions/{session_id}")
def revoke_session(session_id: str, auth: AuthContext = Depends(current_auth)) -> dict:
    changed = runtime.identity.revoke_session(account_id=auth.account_id, session_id=session_id)
    if not changed:
        raise HTTPException(status_code=404, detail="session_not_found_or_inactive")
    runtime.audit.write(actor_id=auth.account_id, action="identity.session.revoked", entity_type="session", entity_id=session_id)
    return {"revoked": True}


@router.post("/logout-all")
def logout_all(auth: AuthContext = Depends(current_auth)) -> dict:
    count = runtime.identity.logout_all(auth.account_id)
    runtime.audit.write(actor_id=auth.account_id, action="identity.logout_all", entity_type="account", entity_id=auth.account_id, metadata={"sessions_revoked": count})
    return {"sessions_revoked": count}


@router.post("/change-password")
def change_password(req: ChangePasswordRequest, auth: AuthContext = Depends(current_auth)) -> dict:
    try:
        runtime.identity.change_password(account_id=auth.account_id, current_password=req.current_password, new_password=req.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    runtime.audit.write(actor_id=auth.account_id, action="identity.password.changed", entity_type="account", entity_id=auth.account_id)
    return {"changed": True, "reauthentication_required": True}


@router.post("/recovery/request", status_code=202)
def request_recovery(req: RecoveryRequest, request: Request) -> dict:
    key = f"recovery:{request.client.host if request.client else 'unknown'}:{req.login.strip().lower()}"
    try:
        runtime.rate_limiter.check(key=key, limit=4, window_seconds=3600)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail="too_many_attempts") from exc
    try:
        challenge_id = runtime.identity.request_password_recovery(req.login)
    except ValueError as exc:
        if str(exc) == "recovery_not_configured":
            raise HTTPException(status_code=503, detail="recovery_not_configured") from exc
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"accepted": True, "challenge_id": challenge_id}


@router.post("/recovery/confirm")
def confirm_recovery(req: RecoveryConfirmRequest) -> dict:
    try:
        runtime.identity.confirm_password_recovery(challenge_id=req.challenge_id, code=req.code, new_password=req.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"changed": True, "reauthentication_required": True}
