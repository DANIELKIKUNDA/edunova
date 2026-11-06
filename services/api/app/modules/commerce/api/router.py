from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.modules.commerce.domain.model import PaymentState
from app.modules.commerce.domain.access_policy import AccessPolicy
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.runtime import runtime
from app.shared.security.rate_limit import RateLimitExceeded

router = APIRouter()


class CheckoutRequest(BaseModel):
    plan_code: str = "premium-30d"
    phone_number: str = Field(min_length=6, max_length=32)
    provider: str = "sandbox-mobile-money"


class CheckoutResponse(BaseModel):
    payment_id: str
    state: str
    amount_cdf: int
    provider: str
    provider_reference: str | None
    expires_at: datetime
    action_type: str
    action_value: str | None
    user_message: str


class ConsumeAiRequest(BaseModel):
    credits: int = Field(ge=1, le=100)


@router.get("/access-policy")
def access_policy() -> dict:
    return AccessPolicy().as_dict()


@router.get("/providers")
def providers() -> list[dict]:
    return [{"code": name, "label": "Mobile Money", "environment": "sandbox" if name.startswith("sandbox") else "production"} for name in runtime.payment_providers]


@router.get("/plans")
def plans() -> list[dict]:
    return [
        {
            "code": p.code,
            "kind": p.kind,
            "name": p.name,
            "price_cdf": p.price.amount,
            "duration_days": p.duration_days,
            "included_ai_credits": p.included_ai_credits,
            "max_personal_documents": p.max_personal_documents,
            "offline_enabled": p.offline_enabled,
        }
        for p in runtime.catalog.list() if p.kind == "subscription"
    ]


@router.get("/ai-packs")
def ai_packs() -> list[dict]:
    return [{"code": p.code, "kind": p.kind, "name": p.name, "price_cdf": p.price.amount, "credits": p.included_ai_credits} for p in runtime.catalog.list() if p.kind == "ai_pack"]


@router.post("/checkout", response_model=CheckoutResponse)
def checkout(
    req: CheckoutRequest,
    auth: AuthContext = Depends(current_auth),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> CheckoutResponse:
    try:
        runtime.rate_limiter.check(key=f"checkout:{auth.account_id}", limit=8, window_seconds=600)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail="too_many_payment_attempts") from exc
    if not idempotency_key or len(idempotency_key) < 8:
        raise HTTPException(status_code=400, detail="Idempotency-Key required")
    try:
        result = runtime.commerce.create_checkout(
            account_id=auth.account_id,
            plan_code=req.plan_code,
            phone_number=req.phone_number,
            idempotency_key=idempotency_key,
            provider_name=req.provider,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    p = result.payment
    runtime.audit.write(actor_id=auth.account_id, action="commerce.checkout.created", entity_type="payment", entity_id=p.id, metadata={"provider": p.provider, "amount_cdf": p.amount.amount})
    return CheckoutResponse(
        payment_id=p.id,
        state=p.state.value,
        amount_cdf=p.amount.amount,
        provider=p.provider,
        provider_reference=p.provider_reference,
        expires_at=p.expires_at,
        action_type=result.action_type,
        action_value=result.action_value,
        user_message=result.user_message,
    )


@router.get("/payments/{payment_id}")
def payment_status(payment_id: str, auth: AuthContext = Depends(current_auth)) -> dict:
    p = runtime.payments.get(payment_id)
    if not p or p.account_id != auth.account_id:
        raise HTTPException(status_code=404, detail="payment_not_found")
    return {
        "id": p.id,
        "state": p.state.value,
        "amount_cdf": p.amount.amount,
        "provider": p.provider,
        "provider_reference": p.provider_reference,
        "updated_at": p.updated_at,
    }


@router.get("/entitlement")
def entitlement(auth: AuthContext = Depends(current_auth)) -> dict:
    s = runtime.commerce.snapshot(auth.account_id)
    return {
        "premium": s.premium,
        "premium_until": s.premium_until,
        "ai_credits_remaining": s.ai_credits_remaining,
        "issued_at": s.issued_at,
        "offline_valid_until": s.valid_until,
        "revision": s.revision,
    }


@router.get("/combined-access")
def combined_access(institution_id: str | None = None, auth: AuthContext = Depends(current_auth)) -> dict:
    """Account-scoped rights; a Campus seat is implicitly held by each active student
    membership while the institution's active student count fits its license.
    This is a read-only presentation snapshot, never an authorization bypass.
    """
    from datetime import datetime, timezone
    from app.modules.commerce.domain.combined_access import resolve_combined_access
    from app.modules.campus.domain.model import CampusRole, InstitutionState, MembershipState

    snapshot = runtime.commerce.snapshot(auth.account_id)
    now = datetime.now(timezone.utc)
    active_member = False
    active_institution = False
    licensed_until = None
    seat_available = False
    if institution_id:
        member = runtime.campus_repo.membership(institution_id, auth.account_id)
        institution = runtime.campus_repo.institution(institution_id)
        active_member = bool(member and member.state == MembershipState.ACTIVE and member.role == CampusRole.STUDENT)
        active_institution = bool(institution and institution.state == InstitutionState.ACTIVE)
        if active_member and active_institution:
            license = runtime.commercial.repo.current_license(institution_id)
            if license and license.permits(now, runtime.campus_repo.overview(institution_id)['students_active']):
                # The current Campus schema uses an implicit seat model: one seat
                # per active student, bounded by the licensed total.
                seat_available = True
                licensed_until = license.ends_at if now < license.ends_at else license.grace_until
    return resolve_combined_access(
        now=now, personal_premium_until=snapshot.premium_until if snapshot.premium else None,
        verified_active_membership=active_member, institution_id=institution_id,
        campus_license_until=licensed_until, campus_institution_active=active_institution,
        campus_seat_assigned=seat_available,
    ).as_dict()


@router.get("/receipts")
def receipts(auth: AuthContext = Depends(current_auth)) -> list[dict]:
    return [
        {
            "id": r.id,
            "payment_id": r.payment_id,
            "amount_cdf": r.amount.amount,
            "issued_at": r.issued_at,
            "description": r.description,
        }
        for r in runtime.receipts.list_for_account(auth.account_id)
    ]


@router.post("/ai/consume")
def consume_ai(req: ConsumeAiRequest, auth: AuthContext = Depends(current_auth)) -> dict:
    try:
        remaining = runtime.commerce.consume_ai_credits(account_id=auth.account_id, credits=req.credits)
    except ValueError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    return {"remaining": remaining}


@router.post("/webhooks/{provider_name}")
async def webhook(provider_name: str, request: Request) -> dict:
    provider = runtime.payment_providers.get(provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail="unknown_provider")
    raw = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    if not provider.verify_webhook(headers, raw):
        raise HTTPException(status_code=401, detail="invalid_webhook_signature")
    try:
        event = provider.parse_webhook(raw)
        if runtime.campus_paid.is_campus_payment(provider_name, event.provider_reference):
            return runtime.campus_paid.verified_event(provider_name=provider_name, event=event)
        payment = runtime.commerce.process_webhook(provider_name=provider_name, event=event)
        runtime.audit.write(actor_id=payment.account_id, action=f"commerce.payment.{payment.state.value}", entity_type="payment", entity_id=payment.id, metadata={"provider": provider_name})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"accepted": True, "payment_id": payment.id, "state": payment.state.value}

class CampusLicenseRequest(BaseModel):
    plan_code:str='campus-annual'; seats:int=Field(ge=1,le=100000); price_cdf:int=Field(ge=0); duration_days:int=Field(default=365,ge=1,le=3660); grace_days:int=Field(default=14,ge=0,le=90)
class PartnerRequest(BaseModel):
    name:str=Field(min_length=2,max_length=160); share_bps:int=Field(ge=0,le=10000)
class ShareRuleRequest(BaseModel):
    partner_id:str; share_bps:int=Field(ge=0,le=10000); product_code:str|None=None

@router.post('/campus/{institution_id}/licenses')
def create_campus_license(institution_id:str, req:CampusLicenseRequest, auth:AuthContext=Depends(current_auth)) -> dict:
    # A quoted price or an administrator's request is not proof of payment.
    # Paid issuance must use a future verified-payment fulfillment path.
    if req.price_cdf > 0:
        raise HTTPException(status_code=409, detail='verified_payment_required_for_paid_campus_license')
    try:x=runtime.commercial.create_license(institution_id=institution_id,actor_id=auth.account_id,plan_code=req.plan_code,seats=req.seats,price_cdf=req.price_cdf,duration_days=req.duration_days,grace_days=req.grace_days)
    except PermissionError as exc:raise HTTPException(status_code=403,detail=str(exc)) from exc
    return {'id':x.id,'institution_id':x.institution_id,'state':x.state.value,'seats':x.seats,'price_cdf':x.price_cdf,'starts_at':x.starts_at,'ends_at':x.ends_at,'grace_until':x.grace_until}

class CampusRenewalRequest(CampusLicenseRequest):
    renewal_reference: str = Field(min_length=1, max_length=128)

@router.post('/campus/{institution_id}/licenses/renew')
def renew_campus_license(institution_id: str, req: CampusRenewalRequest, auth: AuthContext = Depends(current_auth)) -> dict:
    # Paid renewals must be fulfilled from a verified payment event, never
    # from an administrator-supplied reference or price. This endpoint is
    # restricted to zero-price administrative provisioning until that flow exists.
    if req.price_cdf > 0:
        raise HTTPException(status_code=409, detail='verified_payment_required_for_paid_campus_renewal')
    try:
        x = runtime.commercial.renew_license(
            institution_id=institution_id, actor_id=auth.account_id,
            renewal_reference=req.renewal_reference, plan_code=req.plan_code,
            seats=req.seats, price_cdf=req.price_cdf,
            duration_days=req.duration_days, grace_days=req.grace_days,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409 if str(exc) in {'renewal_reference_conflict','license_suspended_or_canceled'} else 422, detail=str(exc)) from exc
    return {'id': x.id, 'institution_id': x.institution_id, 'state': x.state.value,
            'seats': x.seats, 'price_cdf': x.price_cdf, 'starts_at': x.starts_at,
            'ends_at': x.ends_at, 'grace_until': x.grace_until,
            'payment_verified': False}

@router.get('/campus/{institution_id}/license')
def campus_license_status(institution_id:str, auth:AuthContext=Depends(current_auth)) -> dict:
    from app.modules.campus.domain.model import MembershipState
    m=runtime.campus_repo.membership(institution_id,auth.account_id)
    if not m or m.state != MembershipState.ACTIVE:
        raise HTTPException(status_code=403,detail='active_campus_membership_required')
    x=runtime.commercial.license_status(institution_id); lic=x.pop('license')
    return x|({'license':None} if not lic else {'license':{'id':lic.id,'state':lic.state.value,'seats':lic.seats,'ends_at':lic.ends_at,'grace_until':lic.grace_until}})

@router.post('/campus/{institution_id}/partners')
def create_partner(institution_id:str,req:PartnerRequest,auth:AuthContext=Depends(current_auth)) -> dict:
    try:p=runtime.commercial.create_partner(actor_id=auth.account_id,institution_id=institution_id,name=req.name,share_bps=req.share_bps)
    except PermissionError as exc:raise HTTPException(status_code=403,detail=str(exc)) from exc
    return {'id':p.id,'name':p.name,'share_bps':p.share_bps,'state':p.state.value}

@router.post('/campus/{institution_id}/revenue-share-rules')
def create_share_rule(institution_id:str,req:ShareRuleRequest,auth:AuthContext=Depends(current_auth)) -> dict:
    try:r=runtime.commercial.create_share_rule(actor_id=auth.account_id,institution_id=institution_id,partner_id=req.partner_id,share_bps=req.share_bps,product_code=req.product_code)
    except PermissionError as exc:raise HTTPException(status_code=403,detail=str(exc)) from exc
    return {'id':r.id,'partner_id':r.partner_id,'share_bps':r.share_bps,'product_code':r.product_code}

@router.get('/campus/{institution_id}/commercial-overview')
def campus_commercial_overview(institution_id: str, auth: AuthContext = Depends(current_auth)) -> dict:
    """Administrative, read-only commercial snapshot; never exposes student payments."""
    from app.modules.campus.domain.model import InstitutionState
    institution = runtime.campus_repo.institution(institution_id)
    if not institution:
        raise HTTPException(status_code=404, detail='institution_not_found')
    try:
        runtime.commercial._admin(institution_id, auth.account_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    status = runtime.commercial.license_status(institution_id)
    license = status['license']
    return {
        'institution_id': institution_id,
        'institution_active': institution.state == InstitutionState.ACTIVE,
        'license_state': status['effective_state'],
        'licensed_seats': license.seats if license else 0,
        'active_students': status['active_students'],
        'seat_overage': status['seat_overage'],
        'access_permitted': bool(status['permitted'] and institution.state == InstitutionState.ACTIVE),
        'license_ends_at': license.ends_at if license else None,
        'grace_until': license.grace_until if license else None,
        'paid_renewal_available': False,
        'paid_renewal_unavailable_reason': 'verified_campus_payment_fulfillment_not_configured',
    }

# Phase 18: centrally governed, versioned Campus offer catalogue.
# This catalogue is informational; it never issues a paid licence or confirms money.
class CampusOfferInput(BaseModel):
    label: str = Field(min_length=1, max_length=160)
    price_cdf: int = Field(ge=0)
    seats: int = Field(ge=1, le=100000)
    duration_days: int = Field(ge=1, le=3660)
    grace_days: int = Field(ge=0, le=90)
    active: bool = False
    expected_revision: int = Field(ge=0)

@router.get('/platform/campus-offers')
def list_campus_offers(auth: AuthContext = Depends(current_auth)) -> list[dict]:
    from dataclasses import asdict
    try:
        return [asdict(x) for x in runtime.campus_offers.list(actor_id=auth.account_id)]
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

@router.put('/platform/campus-offers/{code}')
def put_campus_offer(code: str, req: CampusOfferInput, auth: AuthContext = Depends(current_auth)) -> dict:
    from dataclasses import asdict
    from app.modules.commerce.application.campus_offers import CampusOffer
    try:
        offer = CampusOffer(code=code, label=req.label, price_cdf=req.price_cdf,
            seats=req.seats, duration_days=req.duration_days, grace_days=req.grace_days,
            active=req.active, revision=req.expected_revision + 1)
        result = runtime.campus_offers.put(actor_id=auth.account_id,
            offer=offer, expected_revision=req.expected_revision)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409 if str(exc) == 'campus_offer_revision_conflict' else 422,
                            detail=str(exc)) from exc
    return asdict(result)


class CampusPaidCheckoutInput(BaseModel):
    offer_code: str = Field(min_length=1, max_length=64)
    phone_number: str = Field(min_length=6, max_length=32)
    provider: str = 'sandbox-mobile-money'

@router.post('/campus/{institution_id}/paid-checkout')
def campus_paid_checkout(institution_id: str, req: CampusPaidCheckoutInput, auth: AuthContext = Depends(current_auth), idempotency_key: str | None = Header(default=None, alias='Idempotency-Key')) -> dict:
    try:
        runtime.rate_limiter.check(key=f'campus-checkout:{auth.account_id}', limit=8, window_seconds=600)
        return runtime.campus_paid.checkout(institution_id=institution_id, actor_id=auth.account_id, offer_code=req.offer_code, phone_number=req.phone_number, provider_name=req.provider, idempotency_key=idempotency_key)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail='too_many_payment_attempts') from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409 if str(exc)=='idempotency_key_conflict' else 422, detail=str(exc)) from exc

@router.get('/campus/{institution_id}/paid-orders/{order_id}')
def campus_paid_order_status(institution_id: str, order_id: str, auth: AuthContext = Depends(current_auth)) -> dict:
    try:
        return runtime.campus_paid.status(institution_id=institution_id, actor_id=auth.account_id, order_id=order_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get('/campus/public-offers')
def public_campus_offers() -> list[dict]:
    """Only active paid offers; never expose governance-only draft offers."""
    from sqlalchemy import select
    from app.modules.commerce.application.campus_offers import CampusOfferRow
    with runtime.sessions() as session:
        offers = session.scalars(select(CampusOfferRow).where(CampusOfferRow.active.is_(True), CampusOfferRow.price_cdf > 0).order_by(CampusOfferRow.price_cdf)).all()
        return [{'code':o.code,'label':o.label,'price_cdf':o.price_cdf,'seats':o.seats,'duration_days':o.duration_days,'grace_days':o.grace_days} for o in offers]
