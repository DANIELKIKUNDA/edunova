from __future__ import annotations

from dataclasses import dataclass

from app.modules.identity.application.ports import AccountRepository, TokenIssuer
from app.modules.identity.domain.model import AccountState


@dataclass(frozen=True)
class AuthContext:
    account_id: str


class Authenticator:
    def __init__(self, *, accounts: AccountRepository, tokens: TokenIssuer) -> None:
        self.accounts = accounts
        self.tokens = tokens

    def authenticate(self, token: str) -> AuthContext:
        payload = self.tokens.decode_access(token)
        if payload.get("typ") != "access":
            raise ValueError("invalid_access_token")
        account = self.accounts.get(str(payload["sub"]))
        if not account or account.state != AccountState.ACTIVE:
            raise ValueError("account_not_active")
        if int(payload.get("ver", 0)) != account.token_version:
            raise ValueError("token_revoked")
        return AuthContext(account_id=account.id)
