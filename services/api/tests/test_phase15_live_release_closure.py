"""Phase 15 closure: adversarial tests of permanent live disclosure commitments."""
from sqlalchemy import select
from app.modules.gradebook.infrastructure.sqlalchemy_repo import MarkRow
from app.modules.campus.infrastructure.sqlalchemy_repo import EnrollmentRow
from app.modules.institutional_analytics.infrastructure.sqlalchemy_repo import InstitutionalAnalyticsLiveReleaseRow
from test_phase15_temporal_archive_integrity import _ready
from test_phase15_institutional_intelligence import _add_students
from test_phase15_source_lineage_completeness import _gradebook


def test_stable_live_release_is_repeatable_across_all_governed_views():
    _,ia,i,p,_,off,kw=_ready()
    first=ia.decision_brief('owner',i.id,**kw)
    assert first['metrics']['results.pass_rate']['value']==100
    again=ia.decision_brief('owner',i.id,**kw)
    assert again['metrics']['results.pass_rate']==first['metrics']['results.pass_rate']
    assert ia.dashboard('owner',i.id,**kw)['results']['pass_rate']==100
    assert ia.executive_readout('owner',i.id,**kw)['quality']['status']=='eligible'
    assert 'results,pass_rate,100' in ia.export_csv('owner',i.id,**kw)
    with ia.repo.sf() as s:
        rows=s.scalars(select(InstitutionalAnalyticsLiveReleaseRow)).all()
    assert len(rows)==1 and rows[0].institution_id==i.id
    assert 'student' not in rows[0].scope_json
    assert len(rows[0].disclosure_hmac)==64


def test_grades_change_after_a_live_release_suppresses_every_derived_route():
    _,ia,i,p,co,off,kw=_ready()
    ia.dashboard('owner',i.id,**kw)  # first published rate is 100%
    with ia.repo.sf() as s:
        rows=s.scalars(select(MarkRow).where(MarkRow.institution_id==i.id)).all()
        assert len(rows)>=5
        for row in rows:row.score=0
        s.commit()
    brief=ia.decision_brief('owner',i.id,**kw)
    assert brief['data_quality']['status']=='temporal_disclosure_suppressed'
    assert brief['data_quality']['unique_active_students'] is None
    for m in brief['metrics'].values():
        assert m['value'] is None
        assert m['denominator'] is None
        assert m['source_fingerprint_sha256'] is None
        assert m['population_reach']['percent'] is None
    assert brief['findings']==[]
    board=ia.dashboard('owner',i.id,**kw)
    assert board['results']['pass_rate'] is None
    assert board['results']['complete_results'] is None
    assert ia.signals('owner',i.id,**kw)==()
    assert ia.executive_readout('owner',i.id,**kw)['priorities']==[]
    assert 'results,pass_rate,\r\n' in ia.export_csv('owner',i.id,**kw)


def test_student_population_rotation_blocks_disclosure_even_same_size():
    cs,ia,i,p,co,off,kw=_ready()
    ia.decision_brief('owner',i.id,**kw)
    _add_students(cs,i.id,co.id,'replacement')
    with ia.repo.sf() as s:
        row=s.scalar(select(EnrollmentRow).where(EnrollmentRow.institution_id==i.id,
            EnrollmentRow.cohort_id==co.id,EnrollmentRow.student_account_id=='a5'))
        row.active=False;s.commit()
    assert ia.repo.distinct_active_students(i.id,p.id,offering_id=off.id)==5
    assert ia.decision_brief('owner',i.id,**kw)['data_quality']['status']=='temporal_disclosure_suppressed'


def test_corrupt_release_commitment_must_fail_closed():
    _,ia,i,p,co,off,kw=_ready()
    assert ia.decision_brief('owner',i.id,**kw)['metrics']['results.pass_rate']['value']==100
    with ia.repo.sf() as s:
        row=s.scalar(select(InstitutionalAnalyticsLiveReleaseRow))
        row.disclosure_hmac='f'*64;s.commit()
    assert ia.decision_brief('owner',i.id,**kw)['data_quality']['status']=='temporal_disclosure_suppressed'


def test_rotation_of_signing_key_suppresses_live_metrics(monkeypatch):
    _,ia,i,p,co,off,kw=_ready()
    ia.decision_brief('owner',i.id,**kw)
    monkeypatch.setenv('INSTITUTIONAL_ANALYTICS_HMAC_SECRET','new-key-'+'a'*64)
    assert ia.dashboard('owner',i.id,**kw)['privacy']['status']=='temporal_disclosure_suppressed'


def test_cross_tenant_enrollment_never_invalidates_live_commitment():
    from uuid import uuid4
    from test_institutional_analytics_lot27 import NOW
    _,ia,i,p,co,off,kw=_ready()
    ia.decision_brief('owner',i.id,**kw)
    with ia.repo.sf() as s:
        s.add(EnrollmentRow(id=uuid4().hex,institution_id='another-tenant',
            cohort_id=co.id,student_account_id='outsider',active=True,created_at=NOW))
        s.commit()
    assert ia.decision_brief('owner',i.id,**kw)['metrics']['results.pass_rate']['value']==100


def test_scoped_archive_oldest_only_even_when_limit_one():
    _,ia,i,p,co,off,kw=_ready()
    first=ia.capture_snapshot('owner',i.id,**kw)
    later=ia.capture_snapshot('owner',i.id,**kw)
    xs=ia.history('owner',i.id,scope_type='offering',scope_id=off.id,
                  academic_period_id=p.id,limit=1)
    assert len(xs)==1 and xs[0]['id']==later['id']
    assert xs[0]['payload'] is None and xs[0]['privacy_status']=='historical_temporal_suppressed'
    both=ia.history('owner',i.id,scope_type='offering',scope_id=off.id,
                    academic_period_id=p.id,limit=20)
    assert next(x for x in both if x['id']==first['id'])['payload'] is not None
    assert sum(x['payload'] is not None for x in both)==1


def test_rbac_denial_does_not_create_release_rows():
    import pytest
    _,ia,i,p,co,off,kw=_ready()
    with pytest.raises(PermissionError):
        ia.decision_brief('student',i.id,**kw)
    with ia.repo.sf() as s:
        assert not s.scalars(select(InstitutionalAnalyticsLiveReleaseRow)).all()


def test_rehashing_manipulated_archive_content_cannot_defeat_keyed_proof():
    from hashlib import sha256
    import json
    from sqlalchemy import select
    from app.modules.institutional_analytics.infrastructure.sqlalchemy_repo import InstitutionalAnalyticsSnapshotRow
    _,ia,i,p,co,off,kw=_ready()
    snap=ia.capture_snapshot('owner',i.id,**kw)
    with ia.repo.sf() as s:
        row=s.get(InstitutionalAnalyticsSnapshotRow,snap['id'])
        original=json.loads(row.payload_json)
        assert original['_internal_archive_proof']['payload_hmac']
        original['results']['pass_rate']=15
        row.payload_json=json.dumps(original,sort_keys=True,separators=(',',':'),ensure_ascii=False)
        row.source_watermark=sha256(row.payload_json.encode()).hexdigest()
        s.commit()
    shown=ia.history('owner',i.id,scope_type='offering',scope_id=off.id,
                     academic_period_id=p.id)[0]
    assert shown['payload'] is None
    assert shown['content_sha256'] is None
    assert shown['privacy_status']=='capture_population_or_integrity_changed'


def test_live_commitment_normalizes_optional_period_filter():
    _,ia,i,p,co,off,kw=_ready()
    # Same institution/offering but optional period cannot create a second
    # first-release slot after the marks have changed.
    first=ia.decision_brief('owner',i.id,offering_id=off.id)
    assert first['metrics']['results.pass_rate']['value']==100
    with ia.repo.sf() as s:
        for row in s.scalars(select(MarkRow).where(MarkRow.institution_id==i.id)):
            row.score=0
        s.commit()
    with_period=ia.decision_brief('owner',i.id,**kw)
    assert with_period['data_quality']['status']=='temporal_disclosure_suppressed'
    with ia.repo.sf() as s:
        assert len(s.scalars(select(InstitutionalAnalyticsLiveReleaseRow)).all())==1


def test_pre_v5_archive_remains_stored_but_is_not_republished():
    _,ia,i,p,co,off,kw=_ready()
    payload=ia.dashboard('owner',i.id,**kw)
    row=ia.repo.save_immutable_snapshot(i.id,payload,'offering',off.id,p.id,
        metric_contract_version=4,private_proof={'version':4,'nonce':'1'*48,'membership_hmac':'2'*64})
    item=ia.history('owner',i.id,scope_type='offering',scope_id=off.id,
        academic_period_id=p.id)[0]
    assert item['id']==row['id']
    assert item['privacy_status']=='legacy_unverified_snapshot'
    assert item['payload'] is None
