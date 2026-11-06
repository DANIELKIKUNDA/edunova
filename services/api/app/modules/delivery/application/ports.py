from __future__ import annotations

from datetime import datetime
from typing import BinaryIO, Protocol

from app.modules.delivery.domain.model import ObjectStat


class DeliveryStoragePort(Protocol):
    def stat(self, locator: str) -> ObjectStat: ...
    def presign_get(self, locator: str, *, ttl_seconds: int) -> str | None: ...
    def open_range(self, locator: str, *, start: int, end: int) -> BinaryIO: ...


class DeliveryClock(Protocol):
    def __call__(self) -> datetime: ...
