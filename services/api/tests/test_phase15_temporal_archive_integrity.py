"""v0.50.6: historical releases fail closed on same-size membership churn.

SQLite / SQLAlchemy / FastAPI service tests; no claim of PostgreSQL serializability.
"""
import copy
import json
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.modules.campus.infrastructure.sqlalchemy_repo import EnrollmentRow
from app.modules.institutional_analytics.infrastructure.sqlalchemy_repo import InstitutionalAnalyticsSnapshotRow
from test_institutional_analytics_lot27 import seed, NOW
from test_phase15_institutional_intelligence import _add_students
from test_phase15_source_lineage_completeness import _gradebook


def _ready():
    cs, ts, _, _, _, ia, i, p, co, off = seed()
    _add_students(cs, i.id, co.id, 'a2', 'a3', 'a4', 'a5')
    _gradebook(ia, i, off, ['student', 'a2', 'a3', 'a4', 'a5'])
    kw = dict(academic_period_id=p.id, offering_id=off.id)
    return cs, ia, i, p, co, off, kw


def _history(ia,i,off,period_id=None):
    return ia.history('owner', i.id, scope_type='offering', scope_id=off.id,
                      academic_period_id=period_id)


def test_archive_v4_preserves_only_public_metrics_without_proof():
    _, ia, i, p, co, off, kw = _ready()
    created=ia.capture_snapshot('owner', i.id, **kw)
    assert created['metric_contract_version']==5
    assert created['payload']['results']['pass_rate']==100
    assert '_internal_archive_proof' not in str(created)
    item=_history(ia,i,off,p.id)[0]
    assert item['privacy_status']=='governed_current_archive'
    assert item['payload']==created['payload']
    assert '_internal_archive_proof' not in str(item)
    assert len(item['content_sha256'])==64


def test_original_snapshot_payload_is_unchanged_by_internal_proof():
    _, ia, i, p, co, off, kw = _ready()
    created=ia.capture_snapshot('owner', i.id, **kw)
    with ia.repo.sf() as db:
        row=db.get(InstitutionalAnalyticsSnapshotRow,created['id'])
        stored=json.loads(row.payload_json)
    proof=stored.pop('_internal_archive_proof')
    assert proof['version']==5
    assert len(proof['nonce'])==48 and len(proof['membership_hmac'])==64
    assert stored==created['payload']
    assert set(proof)=={'nonce','membership_hmac','payload_hmac','version'}
    assert all(c in '0123456789abcdef' for c in proof['membership_hmac'])


def test_same_size_membership_rotation_invalidates_old_rates():
    cs, ia, i, p, co, off, kw = _ready()
    ia.capture_snapshot('owner',i.id,**kw)
    _add_students(cs,i.id,co.id,'a6')
    with ia.repo.sf() as db:
        student=db.scalar(select(EnrollmentRow).where(EnrollmentRow.institution_id==i.id,
            EnrollmentRow.cohort_id==co.id,EnrollmentRow.student_account_id=='a5'))
        student.active=False
        db.commit()
    assert ia.repo.distinct_active_students(i.id,p.id,offering_id=off.id)==5
    assert ia.dashboard('owner',i.id,**kw)['privacy']['status']=='temporal_disclosure_suppressed'  # stronger v0.50.7 contract
    item=_history(ia,i,off,p.id)[0]
    assert item['privacy_status'] in ('capture_population_or_integrity_changed','current_scope_suppressed')
    assert item['payload'] is None and item['content_sha256'] is None


def test_cross_tenant_enrollment_does_not_invalidate_proof():
    _,ia,i,p,co,off,kw=_ready()
    ia.capture_snapshot('owner',i.id,**kw)
    with ia.repo.sf() as db:
        db.add(EnrollmentRow(id=uuid4().hex,institution_id='foreign-institution',
            cohort_id=co.id,student_account_id='outsider',active=True,created_at=NOW))
        db.commit()
    assert _history(ia,i,off,p.id)[0]['privacy_status']=='governed_current_archive'


def test_inactive_enrollment_does_not_invalidate_proof():
    _,ia,i,p,co,off,kw=_ready()
    ia.capture_snapshot('owner',i.id,**kw)
    with ia.repo.sf() as db:
        db.add(EnrollmentRow(id=uuid4().hex,institution_id=i.id,
            cohort_id=co.id,student_account_id='outsider',active=False,created_at=NOW))
        db.commit()
    assert _history(ia,i,off,p.id)[0]['privacy_status']=='governed_current_archive'


def test_extra_duplicate_student_enrollment_does_not_count_twice():
    _,ia,i,p,co,off,kw=_ready()
    ia.capture_snapshot('owner',i.id,**kw)
    with ia.repo.sf() as db:
        db.add(EnrollmentRow(id=uuid4().hex,institution_id=i.id,
            cohort_id=co.id,student_account_id='a2',active=True,created_at=NOW))
        with pytest.raises(IntegrityError):
            db.commit()  # DB enforces the unique cohort/student invariant.
    assert _history(ia,i,off,p.id)[0]['privacy_status']=='governed_current_archive'


@pytest.mark.parametrize('mutation', ['payload','digest','nonce','version','proof'])
def test_archive_forgery_or_integrity_mismatch_never_releases(mutation):
    _,ia,i,p,co,off,kw=_ready()
    snap=ia.capture_snapshot('owner',i.id,**kw)
    with ia.repo.sf() as db:
        row=db.get(InstitutionalAnalyticsSnapshotRow,snap['id'])
        obj=json.loads(row.payload_json)
        if mutation=='payload': obj['results']['pass_rate']=13
        elif mutation=='digest': obj['_internal_archive_proof']['membership_hmac']='0'*64
        elif mutation=='nonce': obj['_internal_archive_proof']['nonce']='x'
        elif mutation=='version': obj['_internal_archive_proof']['version']=2
        else: obj.pop('_internal_archive_proof')
        row.payload_json=json.dumps(obj,sort_keys=True,separators=(',',':'))
        db.commit()
    item=_history(ia,i,off,p.id)[0]
    assert item['payload'] is None and item['content_sha256'] is None
    assert item['privacy_status']=='capture_population_or_integrity_changed'
    assert '_internal_archive_proof' not in str(item)


def test_signing_key_rotation_revokes_old_release(monkeypatch):
    _,ia,i,p,co,off,kw=_ready()
    ia.capture_snapshot('owner',i.id,**kw)
    monkeypatch.setenv('INSTITUTIONAL_ANALYTICS_HMAC_SECRET','rotated-'+'Z'*64)
    item=_history(ia,i,off,p.id)[0]
    assert item['privacy_status'] in ('capture_population_or_integrity_changed','current_scope_suppressed')
    assert item['payload'] is None


def test_missing_secret_fails_closed_for_reads_and_new_captures(monkeypatch):
    _,ia,i,p,co,off,kw=_ready()
    ia.capture_snapshot('owner',i.id,**kw)
    monkeypatch.delenv('JWT_SECRET',raising=False)
    monkeypatch.delenv('INSTITUTIONAL_ANALYTICS_HMAC_SECRET',raising=False)
    item=_history(ia,i,off,p.id)[0]
    assert item['payload'] is None
    with pytest.raises(RuntimeError,match='archive_secret_not_configured'):
        ia.capture_snapshot('owner',i.id,**kw)


def test_two_v4_snapshots_prevent_sequential_rate_differencing():
    _,ia,i,p,co,off,kw=_ready()
    ia.capture_snapshot('owner',i.id,**kw)
    ia.capture_snapshot('owner',i.id,**kw)
    items=_history(ia,i,off,p.id)
    assert items[0]['privacy_status']=='historical_temporal_suppressed'
    assert items[1]['privacy_status']=='governed_current_archive'
    assert items[0]['payload'] is None and items[0]['content_sha256'] is None
    comparison=ia.compare_snapshots('owner',i.id,scope_type='offering',scope_id=off.id,academic_period_id=p.id)
    assert comparison['available'] is False
    assert 'deltas' not in comparison
    assert all('payload' not in x for x in comparison['items'])


def test_v3_archive_hidden_even_when_cohort_currently_safe():
    _,ia,i,p,co,off,kw=_ready()
    payload=ia.dashboard('owner',i.id,**kw)
    ia.repo.save_immutable_snapshot(i.id,payload,'offering',off.id,p.id,metric_contract_version=3)
    old=_history(ia,i,off,p.id)[0]
    assert old['privacy_status']=='legacy_unverified_snapshot'
    assert old['payload'] is None and old['content_sha256'] is None


def test_snapshot_without_period_filter_rechecks_stored_period():
    _,ia,i,p,co,off,kw=_ready()
    ia.capture_snapshot('owner',i.id,**kw)
    item=_history(ia,i,off)[0]
    assert item['privacy_status']=='governed_current_archive'
    assert item['payload']['results']['pass_rate']==100


def test_snapshot_scope_rbac_still_rejects_learner():
    _,ia,i,p,co,off,kw=_ready()
    ia.capture_snapshot('owner',i.id,**kw)
    with pytest.raises(PermissionError):
        ia.history('student',i.id,scope_type='offering',scope_id=off.id)
    with pytest.raises(PermissionError):
        ia.compare_snapshots('student',i.id,scope_type='offering',scope_id=off.id)


def test_snapshot_institution_scope_uses_distinct_union():
    _,ia,i,p,co,off,kw=_ready()
    snap=ia.capture_snapshot('owner',i.id,academic_period_id=p.id)
    h=ia.history('owner',i.id,scope_type='institution',academic_period_id=p.id)
    assert len(h)==1 and h[0]['privacy_status']=='governed_current_archive'
    assert h[0]['payload']==snap['payload']


def test_http_archive_v4_never_exposes_population_hmac_or_old_rates(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine as real_engine
    from sqlalchemy.pool import StaticPool
    from app.modules.identity.api.router import current_auth
    from app.modules.identity.application.auth_context import AuthContext
    from app.modules.institutional_analytics.api.router import router
    from app.runtime import runtime
    import test_institutional_analytics_lot27 as lot27

    monkeypatch.setattr(lot27,'create_engine',lambda url:real_engine(url,
        connect_args={'check_same_thread':False},poolclass=StaticPool))
    _,ia,i,p,co,off,kw=_ready()
    monkeypatch.setattr(runtime,'institutional_analytics',ia)
    api=FastAPI();api.include_router(router)
    api.dependency_overrides[current_auth]=lambda:AuthContext(account_id='owner')
    prefix=f'/institutions/{i.id}'
    params={'scope_type':'offering','scope_id':off.id,'academic_period_id':p.id}
    with TestClient(api) as client:
        assert client.post(prefix+'/snapshots',params=kw).status_code==200
        assert client.post(prefix+'/snapshots',params=kw).status_code==200
        response=client.get(prefix+'/snapshots',params=params)
        assert response.status_code==200
        history=response.json()['items']
        assert len(history)==2
        assert history[0]['privacy_status']=='historical_temporal_suppressed'
        assert history[1]['privacy_status']=='governed_current_archive'
        assert history[0]['payload'] is None
        assert '_internal_archive_proof' not in response.text
        assert 'membership_hmac' not in response.text
        compare=client.get(prefix+'/comparisons',params=params)
        assert compare.status_code==200
        assert compare.json()['available'] is False
        assert 'deltas' not in compare.json()
        api.dependency_overrides[current_auth]=lambda:AuthContext(account_id='student')
        assert client.get(prefix+'/snapshots',params=params).status_code==403
        assert client.get(prefix+'/comparisons',params=params).status_code==403


def test_rehashing_tampered_sql_payload_cannot_forge_private_hmac():
    from hashlib import sha256
    _,ia,i,p,co,off,kw=_ready()
    created=ia.capture_snapshot('owner',i.id,**kw)
    with ia.repo.sf() as db:
        row=db.get(InstitutionalAnalyticsSnapshotRow,created['id'])
        document=json.loads(row.payload_json)
        document['_internal_archive_proof']['membership_hmac']='f'*64
        # An ordinary SHA-256 can always be recomputed by a DB-only attacker.
        # The keyed membership attestation must still fail verification.
        row.payload_json=json.dumps(document,sort_keys=True,separators=(',',':'))
        row.source_watermark=sha256(row.payload_json.encode()).hexdigest()
        db.commit()
    result=_history(ia,i,off,p.id)[0]
    assert result['privacy_status']=='capture_population_or_integrity_changed'
    assert result['payload'] is None and result['content_sha256'] is None
