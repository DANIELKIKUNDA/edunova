from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PaymentRequest:
    account_id: str
    amount_cdf: int
    idempotency_key: str
    phone_number: str


@dataclass(frozen=True)
class PaymentResult:
    provider_reference: str
    status: str


class PaymentProvider(Protocol):
    async def create_payment(self, request: PaymentRequest) -> PaymentResult: ...
    async def verify(self, provider_reference: str) -> PaymentResult: ...
