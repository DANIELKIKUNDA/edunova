from __future__ import annotations

import hashlib
import io
import mimetypes
import os
from pathlib import Path

from app.modules.delivery.domain.model import ObjectStat


class LocalFileDeliveryStorage:
    """Development/test object storage using opaque relative locators under one root."""
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, locator: str) -> Path:
        p = (self.root / locator).resolve()
        if self.root not in p.parents and p != self.root:
            raise ValueError("delivery_locator_escape")
        return p

    def stat(self, locator: str) -> ObjectStat:
        p = self._path(locator)
        if not p.is_file():
            raise ValueError("delivery_object_not_found")
        size = p.stat().st_size
        etag = hashlib.sha256(p.read_bytes()).hexdigest()
        return ObjectStat(size_bytes=size, etag=etag, content_type=mimetypes.guess_type(p.name)[0], checksum_sha256=etag)

    def presign_get(self, locator: str, *, ttl_seconds: int) -> str | None:
        return None

    def open_range(self, locator: str, *, start: int, end: int):
        p = self._path(locator)
        f = p.open("rb")
        f.seek(start)
        return _LimitedReader(f, end - start + 1)


class _LimitedReader(io.RawIOBase):
    def __init__(self, wrapped, remaining: int) -> None:
        self.wrapped = wrapped
        self.remaining = remaining

    def readable(self):
        return True

    def read(self, size=-1):
        if self.remaining <= 0:
            return b""
        if size is None or size < 0 or size > self.remaining:
            size = self.remaining
        data = self.wrapped.read(size)
        self.remaining -= len(data)
        if not data:
            self.remaining = 0
        return data

    def close(self):
        try:
            self.wrapped.close()
        finally:
            super().close()


class S3PresignedDeliveryStorage:
    """S3/R2-compatible adapter. Imported lazily so dev/test has no cloud dependency."""
    def __init__(self, *, bucket: str, endpoint_url: str | None = None, region: str | None = None) -> None:
        import boto3
        self.bucket = bucket
        self.client = boto3.client("s3", endpoint_url=endpoint_url or None, region_name=region or None)

    def stat(self, locator: str) -> ObjectStat:
        r = self.client.head_object(Bucket=self.bucket, Key=locator)
        etag = str(r.get("ETag", "")).strip('"') or None
        return ObjectStat(size_bytes=int(r["ContentLength"]), etag=etag, content_type=r.get("ContentType"), checksum_sha256=(r.get("Metadata") or {}).get("sha256"))

    def presign_get(self, locator: str, *, ttl_seconds: int) -> str | None:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": locator},
            ExpiresIn=max(30, min(int(ttl_seconds), 900)),
        )

    def open_range(self, locator: str, *, start: int, end: int):
        r = self.client.get_object(Bucket=self.bucket, Key=locator, Range=f"bytes={start}-{end}")
        return r["Body"]
