from __future__ import annotations

import hashlib
import hmac
import time


class CommerceLibraryAccess:
    def __init__(self, commerce_service) -> None:
        self.commerce = commerce_service

    def is_premium(self, account_id: str) -> bool:
        return bool(self.commerce.snapshot(account_id).premium)


class HmacResourceDelivery:
    """Opaque short-lived delivery token; never exposes the object storage locator."""
    def __init__(self, secret: str) -> None:
        if len(secret) < 16:
            raise ValueError("resource_delivery_secret_too_short")
        self.secret = secret.encode("utf-8")

    def create_delivery_token(self, *, account_id, resource, ttl_seconds: int = 300) -> str:
        exp = int(time.time()) + max(30, min(ttl_seconds, 1800))
        payload = f"{account_id}:{resource.id}:{exp}"
        sig = hmac.new(self.secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
        return f"{resource.id}.{exp}.{sig}"

    def verify_delivery_token(self, *, account_id: str, resource_id: str, token: str, now_epoch: int | None = None) -> bool:
        try:
            token_resource, raw_exp, sig = token.split(".", 2)
            exp = int(raw_exp)
        except Exception:
            return False
        if token_resource != resource_id:
            return False
        now_epoch = int(time.time()) if now_epoch is None else int(now_epoch)
        if now_epoch > exp:
            return False
        payload = f"{account_id}:{resource_id}:{exp}"
        expected = hmac.new(self.secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
        return hmac.compare_digest(sig, expected)
