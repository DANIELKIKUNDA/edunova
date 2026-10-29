from datetime import UTC,datetime
from types import SimpleNamespace as O
from unittest.mock import Mock
import pytest
from app.modules.service_desk.application.service import ServiceDeskService
from app.modules.service_desk.domain.model import *
from app.modules.campus.domain.model import CampusRole,MembershipState
NOW=lambda:datetime(2026,10,9,tzinfo=UTC)
def fx():
 r=Mock();c=Mock();s=Mock();s.get.return_value=O(id='st',institution_id='u',account_id='student')
 c.membership.side_effect=lambda i,a: O(state=MembershipState.ACTIVE,role=CampusRole.STUDENT if a=='student' else CampusRole.RECTOR)
 return ServiceDeskService(r,c,s,NOW),r,c,s
def req(s,r):
 x=s.create('student','u','st','attestation','Attestation de fréquentation','Pour dossier');r.get.return_value=x;return x
def test_student_creates_and_reads_own_request():
 s,r,_,_=fx();x=req(s,r);assert x.state==RequestState.SUBMITTED and x.kind==RequestKind.ATTESTATION;assert s.get('student','u',x.id).id==x.id
def test_cross_student_scope_is_denied():
 s,r,_,st=fx();st.get.return_value=O(id='st',institution_id='u',account_id='other')
 with pytest.raises(PermissionError,match='student_scope'):s.create('student','u','st','transcript','Relevé officiel','')
def test_rejection_and_action_required_need_reason():
 s,r,_,_=fx();x=req(s,r);x=__import__('dataclasses').replace(x,state=RequestState.IN_REVIEW);r.get.return_value=x
 with pytest.raises(ValueError,match='reason_required'):s.transition('rector','u',x.id,'rejected',1,'')
 y=s.transition('rector','u',x.id,'action_required',1,'Joindre copie identité');assert y.decision_reason=='Joindre copie identité'
def test_fulfillment_requires_approval_and_document_integrity():
 s,r,_,_=fx();x=req(s,r)
 with pytest.raises(ValueError,match='not_approved'):s.fulfill('rector','u',x.id,'doc://a','a'*64,1)
 x=__import__('dataclasses').replace(x,state=RequestState.APPROVED);r.get.return_value=x
 with pytest.raises(ValueError,match='sha256_invalid'):s.fulfill('rector','u',x.id,'doc://a','bad',1)
 y=s.fulfill('rector','u',x.id,'doc://attestation','b'*64,1);assert y.state==RequestState.FULFILLED and y.output_sha256=='b'*64
def test_student_cannot_approve_and_concurrency_is_checked():
 s,r,_,_=fx();x=req(s,r)
 with pytest.raises(PermissionError):s.transition('student','u',x.id,'in_review',1,'')
 with pytest.raises(ValueError,match='concurrent_modification'):s.transition('rector','u',x.id,'in_review',99,'')

def test_staff_queue_requires_staff_and_scopes_institution():
 s,r,c,_=fx();r.list_queue.return_value=[]
 with pytest.raises(PermissionError,match='staff_required'):s.queue('student','u')
 assert s.queue('rector','u','submitted',limit=20)==[]
 r.list_queue.assert_called_once_with('u','submitted',None,20,0)
 with pytest.raises(ValueError,match='pagination_invalid'):s.queue('rector','u',limit=500)
 with pytest.raises(ValueError):s.queue('rector','u','not_a_state')

def test_assignment_rejects_non_staff_roles():
 s,r,c,_=fx();x=req(s,r)
 c.membership.side_effect=lambda i,a: O(state=MembershipState.ACTIVE,role=CampusRole.TEACHER if a=='teacher' else CampusRole.RECTOR)
 with pytest.raises(ValueError,match='assignee_invalid'):s.assign('rector','u',x.id,'teacher',1)

def test_dashboard_requires_staff_and_returns_tenant_counts():
 s,r,_,_=fx();r.status_counts.return_value={'institution_id':'u','total':2,'by_status':{'submitted':2}}
 with pytest.raises(PermissionError):s.dashboard('student','u')
 assert s.dashboard('rector','u')['total']==2
 r.status_counts.assert_called_once_with('u')

def test_student_timeline_redacts_internal_assignment_note():
 s,r,_,_=fx();x=req(s,r)
 from dataclasses import replace
 r.events.return_value=[RequestEvent('e1',x.id,'rector','assigned','private-staff-id',NOW()),RequestEvent('e2',x.id,'rector','state.action_required','Please upload ID',NOW())]
 student_events=s.timeline('student','u',x.id)
 assert student_events[0].note is None and student_events[1].note=='Please upload ID'
 assert r.events.return_value[0].note=='private-staff-id'
 assert s.timeline('rector','u',x.id)[0].note=='private-staff-id'

def test_create_uses_atomic_request_and_event_write():
 s,r,_,_=fx();x=s.create('student','u','st','attestation','Attestation officielle','')
 r.create_with_event.assert_called_once()
 saved,event=r.create_with_event.call_args.args
 assert saved.id==x.id and event.request_id==x.id and event.event_type=='submitted'
 assert not r.create.called and not r.add_event.called

def test_transition_uses_atomic_state_and_timeline_write():
 s,r,_,_=fx();x=req(s,r)
 y=s.transition('rector','u',x.id,'in_review',1,'')
 r.save_with_event.assert_called_once()
 saved,expected,event=r.save_with_event.call_args.args
 assert saved.state==RequestState.IN_REVIEW and expected==1 and event.event_type=='state.in_review'
 assert not r.save.called and not r.add_event.called
