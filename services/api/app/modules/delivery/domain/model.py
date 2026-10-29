from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ObjectStat:
    size_bytes: int
    etag: str | None = None
    content_type: str | None = None
    checksum_sha256: str | None = None


@dataclass(frozen=True)
class DeliveryGrant:
    resource_id: str
    url: str
    expires_at: datetime
    size_bytes: int
    checksum_sha256: str | None
    etag: str | None
    content_type: str | None
    supports_range: bool = True
    requires_app_auth: bool = False


@dataclass(frozen=True)
class ByteSlice:
    start: int
    end: int
    total: int

    @property
    def length(self) -> int:
        return self.end - self.start + 1
