from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import VerifyMismatchError

from app.modules.identity.domain.model import Account


class Argon2PasswordHasher:
    def __init__(self) -> None:
        self._hasher = Argon2Hasher(time_cost=3, memory_cost=65536, parallelism=2)

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except VerifyMismatchError:
            return False


class JwtTokenIssuer:
    def __init__(self, *, secret: str, issuer: str = "edunova", access_minutes: int = 15) -> None:
        if len(secret) < 32:
            raise ValueError("JWT_SECRET must have at least 32 characters")
        self.secret = secret
        self.issuer = issuer
        self.access_minutes = access_minutes

    def issue_access(self, account: Account, now: datetime) -> tuple[str, int]:
        ttl = timedelta(minutes=self.access_minutes)
        exp = now + ttl
        payload = {
            "sub": account.id,
            "iss": self.issuer,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "typ": "access",
            "ver": account.token_version,
        }
        return jwt.encode(payload, self.secret, algorithm="HS256"), int(ttl.total_seconds())

    def decode_access(self, token: str) -> dict:
        return jwt.decode(token, self.secret, algorithms=["HS256"], issuer=self.issuer)

    def new_refresh_token(self) -> tuple[str, str]:
        token = secrets.token_urlsafe(48)
        return token, self.hash_refresh(token)

    def hash_refresh(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
