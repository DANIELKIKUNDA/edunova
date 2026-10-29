"""EduNova v0.50.4: SQL-backed peer-cohort overlap suppression.

Targets a cross-query leak not covered by parent-child complements. These
checks do NOT constitute a formal privacy guarantee for arbitrary queries.
"""
from uuid import uuid4
import pytest

from app.modules.campus.domain.model import CampusRole, UnitKind
from app.modules.campus.infrastructure.sqlalchemy_repo import EnrollmentRow
from app.modules.institutional_analytics.api.router import router
from test_institutional_analytics_lot27 import seed, NOW
from test_phase15_hierarchical_privacy_executive import _sibling
from test_phase15_institutional_intelligence import _add_students
from test_phase15_source_lineage_completeness import _gradebook


def _scenario(peer_students):
    cs,ts,_,_,_,ia,i,p,cohort,off=seed()
    _add_students(cs,i.id,cohort.id,'a2','a3','a4','a5')
    _gradebook(ia,i,off,['student','a2','a3','a4','a5'])
    peer,peer_off=_sibling(cs,ts,i,p,cohort,off,peer_students)
    # Extra disjoint population makes *both* parent complements safe. Only
    # the comparison of two overlapping subgroups could reveal 1-2 people.
    _sibling(cs,ts,i,p,cohort,off,['c1','c2','c3','c4','c5'])
    return cs,ts,ia,i,p,cohort,off,peer,peer_off


def test_overlapping_cohorts_and_executive_readout_suppress_single_person_differences():
    cs,ts,ia,i,p,co,off,peer,peer_off=_scenario(['student','a2','a3','a4','b1'])
    parent=ia.decision_brief('owner',i.id,academic_period_id=p.id)
    assert parent['data_quality']['status']=='eligible'
    assert parent['data_quality']['unique_active_students']==11
    for scope in ({'cohort_id':co.id},{'cohort_id':peer.id},
                  {'offering_id':off.id},{'offering_id':peer_off.id}):
        b=ia.decision_brief('owner',i.id,academic_period_id=p.id,**scope)
        assert b['data_quality']['status']=='overlapping_scope_suppressed'
        assert b['data_quality']['unique_active_students'] is None
        assert b['findings']==[]
        assert all(x['status']=='suppressed_overlapping_scope' and x['value'] is None
                   and x['denominator'] is None and x['source_fingerprint_sha256'] is None
                   and x['population_reach']['percent'] is None for x in b['metrics'].values())
        report=ia.executive_readout('owner',i.id,academic_period_id=p.id,**scope)
        assert report['quality']['status']=='overlapping_scope_suppressed'
        assert report['priorities']==[]
        assert all(x['observed_percent'] is None and x['source_fingerprint_sha256'] is None
                   for x in report['indicators'])
        import json
        assert '"b1"' not in json.dumps(b) and '"student"' not in json.dumps(report)


def test_identical_populations_are_not_suppressed_by_peer_guard():
    cs,ts,ia,i,p,co,off,peer,peer_off=_scenario(['student','a2','a3','a4','a5'])
    report=ia.decision_brief('owner',i.id,academic_period_id=p.id,offering_id=off.id)
    assert report['data_quality']['unique_active_students']==5
    assert report['data_quality']['status']=='eligible'
    assert report['metrics']['results.pass_rate']['value']==100


def test_disjoint_peers_do_not_block_valid_institutional_analytics():
    cs,ts,ia,i,p,co,off,peer,peer_off=_scenario(['b1','b2','b3','b4','b5'])
    report=ia.decision_brief('owner',i.id,academic_period_id=p.id,offering_id=off.id)
    assert report['data_quality']['status']=='eligible'
    assert report['metrics']['results.pass_rate']['status']=='available'


def test_two_person_symmetric_difference_is_suppressed():
    cs,ts,ia,i,p,co,off,peer,peer_off=_scenario(['student','a2','a3','b1','b2'])
    report=ia.decision_brief('owner',i.id,academic_period_id=p.id,cohort_id=co.id)
    assert report['data_quality']['status']=='overlapping_scope_suppressed'


def test_unit_versus_member_cohort_with_one_person_difference_suppressed():
    cs,ts,_,_,_,ia,i,p,co,off=seed()
    _add_students(cs,i.id,co.id,'a2','a3','a4','a5')
    _gradebook(ia,i,off,['student','a2','a3','a4','a5'])
    # Both the original cohort and the unit containing it are plausible
    # analytics views. A different cohort inside the unit adds one learner.
    _sibling(cs,ts,i,p,co,off,['student','a2','a3','a4','a5','b1'])
    outside=cs.add_unit('owner',i.id,kind=UnitKind.PROGRAM,name='Other program',code='OTH',parent_id=None)
    other=cs.create_cohort('owner',i.id,program_unit_id=outside.id,
                           academic_period_id=p.id,name='Outside',level='1')
    ts.create_offering('owner',i.id,course_id=off.course_id,cohort_id=other.id,
                       academic_period_id=p.id,label='Other')
    _add_students(cs,i.id,other.id,'c1','c2','c3','c4','c5')
    b=ia.decision_brief('owner',i.id,academic_period_id=p.id,academic_unit_id=co.program_unit_id)
    assert b['data_quality']['status']=='overlapping_scope_suppressed'
    assert all(x['value'] is None for x in b['metrics'].values())


def test_cross_tenant_enrollment_cannot_forge_a_peer_overlap():
    cs,ts,ia,i,p,co,off,peer,peer_off=_scenario(['b1','b2','b3','b4','b5'])
    with ia.repo.sf() as s:
        s.add(EnrollmentRow(id=uuid4().hex,institution_id='some-other-university',
                            cohort_id=peer.id,student_account_id='student',
                            active=True,created_at=NOW))
        s.commit()
    b=ia.decision_brief('owner',i.id,academic_period_id=p.id,offering_id=off.id)
    assert b['data_quality']['status']=='eligible'


def test_inactive_enrollments_cannot_create_peer_overlap():
    cs,ts,ia,i,p,co,off,peer,peer_off=_scenario(['b1','b2','b3','b4','b5'])
    with ia.repo.sf() as s:
        s.add(EnrollmentRow(id=uuid4().hex,institution_id=i.id,
                            cohort_id=peer.id,student_account_id='student',
                            active=False,created_at=NOW))
        s.commit()
    b=ia.decision_brief('owner',i.id,academic_period_id=p.id,offering_id=off.id)
    assert b['data_quality']['status']=='eligible'


def test_same_tenant_rbac_and_authenticated_route_remain_enforced():
    cs,ts,ia,i,p,co,off,peer,peer_off=_scenario(['student','a2','a3','a4','b1'])
    for actor in ('teacher','student'):
        with pytest.raises(PermissionError):
            ia.decision_brief(actor,i.id,offering_id=off.id)
    alien=cs.create_institution('alien-owner',name='Alien University',slug='alien-504',
                                legal_name='',country_code='CD',city='Goma',logo_url=None)
    with pytest.raises(PermissionError):
        ia.decision_brief('alien-owner',i.id,offering_id=off.id)
    with pytest.raises(ValueError,match='offering_not_found'):
        ia.decision_brief('owner',i.id,offering_id='not-from-this-university')
    for path in ('/institutions/{iid}/intelligence/decision-brief',
                 '/institutions/{iid}/intelligence/executive-readout'):
        matches=[r for r in router.routes if r.path==path]
        assert len(matches)==1 and matches[0].methods=={'GET'}
        assert any(d.call.__name__=='current_auth' for d in matches[0].dependant.dependencies)


def test_period_is_inferred_from_offering_for_peer_cohort_check():
    cs,ts,ia,i,p,co,off,peer,peer_off=_scenario(['student','a2','a3','a4','b1'])
    implicit=ia.decision_brief('owner',i.id,offering_id=off.id)
    explicit=ia.decision_brief('owner',i.id,academic_period_id=p.id,offering_id=off.id)
    assert implicit['data_quality']['status']==explicit['data_quality']['status']=='overlapping_scope_suppressed'


def test_peer_with_two_students_cannot_force_suppression_of_large_cohort():
    cs,ts,ia,i,p,co,off,peer,peer_off=_scenario(['student','b1'])
    report=ia.decision_brief('owner',i.id,academic_period_id=p.id,offering_id=off.id)
    assert report['data_quality']['status']=='eligible'
    assert report['metrics']['results.pass_rate']['status']=='available'
