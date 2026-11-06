from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.modules.delivery.application.ports import DeliveryStoragePort
from app.modules.delivery.domain.model import ByteSlice, DeliveryGrant
from app.modules.library.domain.model import LibraryResource


class DeliveryError(ValueError):
    pass


class RangeNotSatisfiable(DeliveryError):
    def __init__(self, total: int) -> None:
        super().__init__("delivery_range_not_satisfiable")
        self.total = total


class DeliveryService:
    """Authorizes delivery without exposing object locators.

    Access is rechecked at grant time. Tokens are short-lived capabilities emitted by
    the library manifest, but they are not sufficient to bypass a later entitlement
    change for premium material.
    """

    def __init__(self, *, library_repository, library_access, token_verifier, storage: DeliveryStoragePort, now=None) -> None:
        self.library_repository = library_repository
        self.library_access = library_access
        self.token_verifier = token_verifier
        self.storage = storage
        self.now = now or (lambda: datetime.now(UTC))

    def _resource(self, resource_id: str) -> LibraryResource:
        resource = self.library_repository.get_resource(resource_id)
        if resource is None or not resource.storage_locator:
            raise DeliveryError("delivery_resource_not_found")
        return resource

    def _authorize(self, *, account_id: str, resource: LibraryResource, token: str) -> None:
        if not self.token_verifier.verify_delivery_token(account_id=account_id, resource_id=resource.id, token=token):
            raise DeliveryError("delivery_token_invalid_or_expired")
        course = self.library_repository.get_course_for_version(resource.version_id)
        if course is None or course.publication_state.value != "published":
            raise DeliveryError("delivery_course_not_published")
        if (course.premium_required or resource.premium_required) and not self.library_access.is_premium(account_id):
            raise DeliveryError("delivery_premium_required")

    def grant(self, *, account_id: str, resource_id: str, token: str, public_base_url: str, ttl_seconds: int = 300, purpose: str = "stream") -> DeliveryGrant:
        resource = self._resource(resource_id)
        self._authorize(account_id=account_id, resource=resource, token=token)
        if purpose not in {"stream", "offline"}:
            raise DeliveryError("delivery_invalid_purpose")
        if purpose == "offline" and not resource.offline_allowed:
            raise DeliveryError("delivery_offline_not_allowed")
        stat = self.storage.stat(resource.storage_locator)
        if resource.size_bytes is not None and stat.size_bytes != resource.size_bytes:
            raise DeliveryError("delivery_size_mismatch")
        if resource.checksum_sha256 and stat.checksum_sha256 and resource.checksum_sha256.lower() != stat.checksum_sha256.lower():
            raise DeliveryError("delivery_storage_checksum_mismatch")
        ttl_seconds = max(30, min(int(ttl_seconds), 900))
        direct = self.storage.presign_get(resource.storage_locator, ttl_seconds=ttl_seconds)
        url = direct or f"{public_base_url.rstrip('/')}/v1/delivery/resources/{resource.id}/content?token={token}"
        return DeliveryGrant(
            resource_id=resource.id,
            url=url,
            expires_at=self.now() + timedelta(seconds=ttl_seconds),
            size_bytes=stat.size_bytes,
            checksum_sha256=resource.checksum_sha256,
            etag=stat.etag,
            content_type=resource.mime_type or stat.content_type,
            supports_range=True,
            requires_app_auth=(direct is None),
        )

    def prepare_proxy(self, *, account_id: str, resource_id: str, token: str, range_header: str | None):
        resource = self._resource(resource_id)
        self._authorize(account_id=account_id, resource=resource, token=token)
        stat = self.storage.stat(resource.storage_locator)
        slice_ = parse_single_range(range_header, stat.size_bytes)
        return resource, stat, slice_


def parse_single_range(header: str | None, total: int) -> ByteSlice:
    if total <= 0:
        raise DeliveryError("delivery_empty_object")
    if not header:
        return ByteSlice(start=0, end=total - 1, total=total)
    raw = header.strip().lower()
    if not raw.startswith("bytes=") or "," in raw:
        raise DeliveryError("delivery_invalid_range")
    spec = raw[6:].strip()
    if "-" not in spec:
        raise DeliveryError("delivery_invalid_range")
    left, right = spec.split("-", 1)
    try:
        if left == "":
            suffix = int(right)
            if suffix <= 0:
                raise DeliveryError("delivery_invalid_range")
            start = max(0, total - suffix)
            end = total - 1
        else:
            start = int(left)
            end = total - 1 if right == "" else int(right)
    except (TypeError, ValueError) as exc:
        raise DeliveryError("delivery_invalid_range") from exc
    if start < 0 or start >= total or end < start:
        raise RangeNotSatisfiable(total)
    end = min(end, total - 1)
    return ByteSlice(start=start, end=end, total=total)
