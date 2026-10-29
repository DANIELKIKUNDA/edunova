"""Adversarial faculty boundary on the canonical Phase 14 service.

Frontend hiding a course is NEVER an authorization mechanism.
"""
import pytest
from app.modules.campus.domain.model import CampusRole, MembershipState
from app.modules.pedagogical_intelligence.application.service import CanonicalPedagogicalIntelligenceService


class Row:
    def __init__(self, **kw): self.__dict__.update(kw)


class Campus:
    def membership(self, iid, actor):
        return Row(role=CampusRole.FACULTY_ADMIN, state=MembershipState.ACTIVE)


class Teaching:
    def __init__(self): self.scopes = []
    def offering(self, iid, oid): return Row(id=oid, cohort_id='cohort1') if iid == 'uni1' else None
    def my_offerings(self, actor, iid):
        self.scopes.append((actor, iid))
        return [Row(id='authorized-faculty-offering')]


class Repo:
    def offering_signal(self, *_args, **_kw):
        return {'curriculum_course_id': 'course1'}
    def upsert_objective(self, *_args): pass
    def map_question(self, *_args): pass
    def bind_blueprint(self, *_args): pass


def test_faculty_admin_cannot_modify_another_faculty_objective():
    teaching=Teaching()
    service=CanonicalPedagogicalIntelligenceService(Repo(), Campus(), teaching)
    with pytest.raises(PermissionError,match='pedintel_faculty_scope_forbidden'):
        service.register_objective('faculty_staff','uni1','foreign-faculty-offering','obj','Title')
    with pytest.raises(PermissionError,match='pedintel_faculty_scope_forbidden'):
        service.map_question('faculty_staff','uni1','foreign-faculty-offering','obj','q1')
    with pytest.raises(PermissionError,match='pedintel_faculty_scope_forbidden'):
        service.bind_blueprint('faculty_staff','uni1','foreign-faculty-offering','b1')
    assert teaching.scopes == [('faculty_staff','uni1')]*3


def test_faculty_admin_can_edit_only_a_scoped_offering():
    service=CanonicalPedagogicalIntelligenceService(Repo(), Campus(), Teaching())
    result=service.register_objective('faculty_staff','uni1','authorized-faculty-offering','obj','Titre')
    assert result['objective_id']=='obj'


def test_faculty_scope_fails_closed_if_authorized_listing_is_unavailable():
    class NoListing(Teaching):
        def my_offerings(self, actor, iid): raise PermissionError('teaching_membership_required')
    service=CanonicalPedagogicalIntelligenceService(Repo(), Campus(), NoListing())
    with pytest.raises(PermissionError):
        service.register_objective('faculty_staff','uni1','foreign-faculty-offering','obj','Titre')
