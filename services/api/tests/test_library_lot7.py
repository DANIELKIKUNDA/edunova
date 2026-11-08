from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.modules.library.domain.model import CourseVersion, LibraryCourse, LibraryResource, PublicationState, ResourceKind
from app.runtime import runtime
from app.modules.identity.application.service import RegisterInput

client = TestClient(app)


def _account(prefix="lib"):
    email=f"{prefix}-{uuid4().hex[:8]}@example.test"
    account, tokens = runtime.identity.register(RegisterInput(display_name="Library User", password="strong-pass-123", email=email, phone_number=None, device_name="pytest"))
    return account.id, {'Authorization':f"Bearer {tokens.access_token}"}


def _seed(*, premium_course=False, premium_resource=False, state=PublicationState.PUBLISHED):
    suffix=uuid4().hex[:8]
    cid=f"course-{suffix}"; vid=f"ver-{suffix}"
    runtime.library_repository.save_version(CourseVersion(id=vid,course_id=cid,label='2026.1',academic_year='2026-2027',source_fingerprint='f'*64,changelog='Initial',published_at=datetime.now(UTC)))
    runtime.library_repository.save_course(LibraryCourse(id=cid,faculty_domain='Médecine',program='Médecine humaine',level='BAC1',semester='S1',title='Anatomie',slug=f'anatomie-{suffix}',description='Cours pilote',publication_state=state,premium_required=premium_course,active_version_id=vid,updated_at=datetime.now(UTC)))
    runtime.library_repository.save_resource(LibraryResource(id=f'res-{suffix}',version_id=vid,kind=ResourceKind.STRUCTURED_COURSE,title='Cours structuré',mime_type='application/json',size_bytes=1024,checksum_sha256='a'*64,premium_required=premium_resource,offline_allowed=True,sort_order=1,storage_locator='s3://private-bucket/secret-key'))
    return cid


def test_catalog_exposes_only_published_courses():
    _, h=_account('catalog')
    published=_seed()
    draft=_seed(state=PublicationState.DRAFT)
    r=client.get('/v1/library/catalog?faculty_domain=M%C3%A9decine',headers=h)
    assert r.status_code==200
    ids={c['id'] for c in r.json()['courses']}
    assert published in ids
    assert draft not in ids


def test_free_user_sees_locked_premium_resource_without_storage_locator_leak():
    _, h=_account('locked')
    cid=_seed(premium_resource=True)
    r=client.get(f'/v1/library/courses/{cid}/manifest',headers=h)
    assert r.status_code==200, r.text
    resource=r.json()['resources'][0]
    assert resource['access']=='locked'
    assert resource['delivery_token'] is None
    assert 'storage_locator' not in resource


def test_free_resource_gets_short_lived_opaque_delivery_token():
    _, h=_account('delivery')
    cid=_seed()
    r=client.get(f'/v1/library/courses/{cid}/manifest',headers=h)
    resource=r.json()['resources'][0]
    assert resource['access']=='available'
    assert resource['offline_allowed'] is True
    token=resource['delivery_token']
    assert token and token.startswith(resource['id'] + '.')
    assert 's3://' not in token


def test_catalog_is_not_bound_to_university_name():
    _, h=_account('multiuni')
    cid=_seed()
    c=client.get(f'/v1/library/courses/{cid}',headers=h).json()
    assert set(['faculty_domain','program','level','semester']).issubset(c)
    assert 'university' not in c

def test_catalog_can_be_browsed_anonymously_for_freemium_discovery():
    cid=_seed()
    r=client.get('/v1/library/catalog?faculty_domain=M%C3%A9decine')
    assert r.status_code==200
    assert cid in {c['id'] for c in r.json()['courses']}

def test_delivery_token_is_bound_to_account_resource_and_expiry():
    from app.modules.library.infrastructure.access import HmacResourceDelivery
    from app.modules.library.domain.model import LibraryResource, ResourceKind
    r=LibraryResource(id='res-secure',version_id='v1',kind=ResourceKind.ORIGINAL,title='x',mime_type='application/pdf',size_bytes=10,checksum_sha256=None,premium_required=False,offline_allowed=True,sort_order=0,storage_locator='secret')
    d=HmacResourceDelivery('this-is-a-long-test-secret')
    token=d.create_delivery_token(account_id='acc-1',resource=r,ttl_seconds=300)
    _, raw_exp, _ = token.split('.',2)
    exp=int(raw_exp)
    assert d.verify_delivery_token(account_id='acc-1',resource_id='res-secure',token=token,now_epoch=exp)
    assert not d.verify_delivery_token(account_id='acc-2',resource_id='res-secure',token=token,now_epoch=exp)
    assert not d.verify_delivery_token(account_id='acc-1',resource_id='other',token=token,now_epoch=exp)
    assert not d.verify_delivery_token(account_id='acc-1',resource_id='res-secure',token=token,now_epoch=exp+1)


def test_catalog_supports_search_pagination_and_etag_revalidation():
    _seed()
    special = _seed()
    # Make one title uniquely searchable.
    course = runtime.library_repository.get_course(special)
    runtime.library_repository.save_course(LibraryCourse(
        id=course.id, faculty_domain=course.faculty_domain, program=course.program, level=course.level,
        semester=course.semester, title='Neuroanatomie avancée', slug=course.slug, description='Système nerveux central',
        publication_state=course.publication_state, premium_required=course.premium_required,
        active_version_id=course.active_version_id, updated_at=datetime.now(UTC),
    ))
    r=client.get('/v1/library/catalog?q=Neuroanatomie&limit=1')
    assert r.status_code==200
    assert [c['id'] for c in r.json()['courses']] == [special]
    etag=r.headers.get('etag')
    assert etag and r.json()['etag']==etag
    cached=client.get('/v1/library/catalog?q=Neuroanatomie&limit=1',headers={'If-None-Match':etag})
    assert cached.status_code==304


def test_catalog_cursor_is_opaque_and_invalid_cursor_is_rejected():
    for _ in range(3): _seed()
    first=client.get('/v1/library/catalog?limit=2')
    assert first.status_code==200
    cursor=first.json()['next_cursor']
    assert cursor is not None and cursor != '2'
    second=client.get('/v1/library/catalog',params={'limit':2,'cursor':cursor})
    assert second.status_code==200
    assert {c['id'] for c in first.json()['courses']}.isdisjoint({c['id'] for c in second.json()['courses']})
    bad=client.get('/v1/library/catalog?cursor=***not-a-cursor***')
    assert bad.status_code==422
    assert bad.json()['detail']=='invalid_library_cursor'


def test_catalog_etag_is_stable_across_pages_and_changes_after_publication():
    for _ in range(4):
        _seed()
    first = client.get('/v1/library/catalog?limit=1')
    assert first.status_code == 200
    etag = first.json()['etag']
    cursor = first.json()['next_cursor']
    assert cursor
    second = client.get('/v1/library/catalog', params={'limit':1, 'cursor':cursor})
    assert second.status_code == 200
    assert second.json()['etag'] == etag
    # Publishing another course changes the fingerprint of the whole filtered catalog.
    _seed()
    changed = client.get('/v1/library/catalog?limit=1')
    assert changed.status_code == 200
    assert changed.json()['etag'] != etag
