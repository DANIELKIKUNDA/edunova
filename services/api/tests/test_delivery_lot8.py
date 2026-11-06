from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.modules.delivery.application.service import DeliveryError, parse_single_range
from app.modules.identity.application.service import RegisterInput
from app.modules.library.domain.model import CourseVersion, LibraryCourse, LibraryResource, PublicationState, ResourceKind
from app.runtime import runtime

client = TestClient(app)


def _account(prefix="d8"):
    account, tokens = runtime.identity.register(RegisterInput(
        display_name="Delivery User", password="strong-pass-123",
        email=f"{prefix}-{uuid4().hex[:8]}@example.test", phone_number=None, device_name="pytest",
    ))
    return account.id, {"Authorization": f"Bearer {tokens.access_token}"}


def _seed_blob(*, premium=False, payload=b"0123456789abcdefghijklmnopqrstuvwxyz"):
    suffix = uuid4().hex[:8]
    cid, vid, rid = f"course-{suffix}", f"ver-{suffix}", f"res-{suffix}"
    locator = f"tests/{rid}.bin"
    path = Path(runtime.delivery_storage.root) / locator
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    sha = hashlib.sha256(payload).hexdigest()
    runtime.library_repository.save_version(CourseVersion(
        id=vid, course_id=cid, label="2026.1", academic_year="2026-2027",
        source_fingerprint="f"*64, changelog="Initial", published_at=datetime.now(UTC),
    ))
    runtime.library_repository.save_course(LibraryCourse(
        id=cid, faculty_domain="Sciences", program="Informatique", level="BAC1", semester="S1",
        title="Algorithmique", slug=f"algo-{suffix}", description="Cours", publication_state=PublicationState.PUBLISHED,
        premium_required=premium, active_version_id=vid, updated_at=datetime.now(UTC),
    ))
    resource = LibraryResource(
        id=rid, version_id=vid, kind=ResourceKind.ORIGINAL, title="Support", mime_type="application/octet-stream",
        size_bytes=len(payload), checksum_sha256=sha, premium_required=premium, offline_allowed=True,
        sort_order=1, storage_locator=locator,
    )
    runtime.library_repository.save_resource(resource)
    return cid, resource, payload


def test_single_range_parser_supports_full_explicit_open_and_suffix_ranges():
    assert parse_single_range(None, 100).start == 0
    p = parse_single_range("bytes=10-19", 100)
    assert (p.start, p.end, p.length) == (10, 19, 10)
    p = parse_single_range("bytes=95-", 100)
    assert (p.start, p.end) == (95, 99)
    p = parse_single_range("bytes=-7", 100)
    assert (p.start, p.end) == (93, 99)


def test_single_range_parser_rejects_multi_range_and_unsatisfiable_ranges():
    for raw in ["bytes=0-1,4-5", "bytes=100-120", "garbage", "bytes=-0"]:
        try:
            parse_single_range(raw, 100)
        except DeliveryError:
            pass
        else:
            raise AssertionError(raw)


def test_delivery_grant_is_opaque_range_capable_and_does_not_expose_locator():
    _, headers = _account("grant")
    cid, resource, _ = _seed_blob()
    manifest = client.get(f"/v1/library/courses/{cid}/manifest", headers=headers).json()
    token = manifest["resources"][0]["delivery_token"]
    r = client.get(f"/v1/delivery/resources/{resource.id}/grant", params={"token": token}, headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["resource_id"] == resource.id
    assert body["supports_range"] is True
    assert body["checksum_sha256"] == resource.checksum_sha256
    assert resource.storage_locator not in r.text
    assert "/v1/delivery/resources/" in body["url"]


def test_proxy_delivery_supports_resume_with_http_range_and_etag():
    _, headers = _account("range")
    cid, resource, payload = _seed_blob()
    manifest = client.get(f"/v1/library/courses/{cid}/manifest", headers=headers).json()
    token = manifest["resources"][0]["delivery_token"]
    r = client.get(
        f"/v1/delivery/resources/{resource.id}/content", params={"token": token},
        headers={**headers, "Range": "bytes=10-19"},
    )
    assert r.status_code == 206, r.text
    assert r.content == payload[10:20]
    assert r.headers["accept-ranges"] == "bytes"
    assert r.headers["content-range"] == f"bytes 10-19/{len(payload)}"
    assert int(r.headers["content-length"]) == 10
    assert r.headers["etag"]


def test_full_delivery_returns_exact_bytes_and_private_no_store():
    _, headers = _account("full")
    cid, resource, payload = _seed_blob()
    manifest = client.get(f"/v1/library/courses/{cid}/manifest", headers=headers).json()
    token = manifest["resources"][0]["delivery_token"]
    r = client.get(f"/v1/delivery/resources/{resource.id}/content", params={"token": token}, headers=headers)
    assert r.status_code == 200
    assert r.content == payload
    assert r.headers["cache-control"] == "private, no-store"


def test_delivery_token_cannot_be_reused_by_another_account():
    _, h1 = _account("owner")
    _, h2 = _account("other")
    cid, resource, _ = _seed_blob()
    token = client.get(f"/v1/library/courses/{cid}/manifest", headers=h1).json()["resources"][0]["delivery_token"]
    r = client.get(f"/v1/delivery/resources/{resource.id}/grant", params={"token": token}, headers=h2)
    assert r.status_code == 403


def test_premium_access_is_rechecked_at_delivery_time():
    account_id, headers = _account("premium")
    _, resource, _ = _seed_blob(premium=True)
    # A forged/previously issued capability alone must not bypass current entitlement.
    token = runtime.resource_delivery.create_delivery_token(account_id=account_id, resource=resource, ttl_seconds=300)
    r = client.get(f"/v1/delivery/resources/{resource.id}/grant", params={"token": token}, headers=headers)
    assert r.status_code == 403
    assert r.json()["detail"] == "delivery_premium_required"


def test_delivery_detects_metadata_size_mismatch_before_download():
    _, headers = _account("mismatch")
    cid, resource, _ = _seed_blob()
    bad = LibraryResource(**{**resource.__dict__, "size_bytes": resource.size_bytes + 1})
    runtime.library_repository.save_resource(bad)
    token = runtime.resource_delivery.create_delivery_token(account_id=runtime.authenticator.authenticate(headers["Authorization"].split()[1]).account_id, resource=bad, ttl_seconds=300)
    r = client.get(f"/v1/delivery/resources/{bad.id}/grant", params={"token": token}, headers=headers)
    assert r.status_code == 422
    assert r.json()["detail"] == "delivery_size_mismatch"

def test_unsatisfiable_range_returns_416_with_total_size():
    _, headers = _account("range416")
    cid, resource, payload = _seed_blob()
    token = client.get(f"/v1/library/courses/{cid}/manifest", headers=headers).json()["resources"][0]["delivery_token"]
    r = client.get(
        f"/v1/delivery/resources/{resource.id}/content",
        params={"token": token},
        headers={**headers, "Range": f"bytes={len(payload)+10}-"},
    )
    assert r.status_code == 416
    assert r.headers["content-range"] == f"bytes */{len(payload)}"

def test_offline_purpose_rejects_resource_not_authorized_for_offline_use():
    account_id, headers = _account("nooffline")
    cid, resource, _ = _seed_blob()
    blocked = LibraryResource(**{**resource.__dict__, "offline_allowed": False})
    runtime.library_repository.save_resource(blocked)
    token = runtime.resource_delivery.create_delivery_token(account_id=account_id, resource=blocked, ttl_seconds=300)
    r = client.get(f"/v1/delivery/resources/{blocked.id}/grant", params={"token": token, "purpose": "offline"}, headers=headers)
    assert r.status_code == 422
    assert r.json()["detail"] == "delivery_offline_not_allowed"


def test_delivery_blocks_when_bucket_checksum_disagrees_with_catalog_checksum():
    account_id, headers = _account("checksum")
    _, resource, _ = _seed_blob()
    bad = LibraryResource(**{**resource.__dict__, "checksum_sha256": "0" * 64})
    runtime.library_repository.save_resource(bad)
    token = runtime.resource_delivery.create_delivery_token(account_id=account_id, resource=bad, ttl_seconds=300)
    r = client.get(f"/v1/delivery/resources/{bad.id}/grant", params={"token": token}, headers=headers)
    assert r.status_code == 422
    assert r.json()["detail"] == "delivery_storage_checksum_mismatch"

def test_local_object_storage_rejects_path_escape():
    from app.modules.delivery.infrastructure.storage import LocalFileDeliveryStorage
    s = LocalFileDeliveryStorage('/tmp/edunova-delivery-safe-root')
    try:
        s.stat('../escape.bin')
    except ValueError as exc:
        assert str(exc) == 'delivery_locator_escape'
    else:
        raise AssertionError('path escape should be rejected')


def test_invalid_delivery_purpose_is_rejected():
    account_id, headers = _account('purpose')
    _, resource, _ = _seed_blob()
    token = runtime.resource_delivery.create_delivery_token(account_id=account_id, resource=resource, ttl_seconds=300)
    r = client.get(f'/v1/delivery/resources/{resource.id}/grant', params={'token':token,'purpose':'backup'}, headers=headers)
    assert r.status_code == 422
    assert r.json()['detail'] == 'delivery_invalid_purpose'


def test_proxy_grant_explicitly_requires_app_auth_header():
    _, headers = _account('authhint')
    cid, resource, _ = _seed_blob()
    token = client.get(f'/v1/library/courses/{cid}/manifest', headers=headers).json()['resources'][0]['delivery_token']
    r = client.get(f'/v1/delivery/resources/{resource.id}/grant', params={'token':token}, headers=headers)
    assert r.status_code == 200
    assert r.json()['requires_app_auth'] is True
