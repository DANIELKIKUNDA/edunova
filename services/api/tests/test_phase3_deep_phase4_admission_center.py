import pytest
from app.runtime import runtime
from app.modules.campus.domain.model import CampusRole
from test_candidate_applications_phase3 import setup_open,consent

def submitted(account='cand-deep'):
 admin,inst,c=setup_open();x=runtime.applications.create(account,c.id,given_names='Grace',family_name='Hopper',email='grace@example.org');d=runtime.applications.upload(account,x.id,'DIPLOME','d.pdf','application/pdf',b'%PDF-1.7\nproof');consent(account,x.id);x=runtime.applications.submit(account,x.id,x.row_version);return admin,inst,x,d

def test_phase3_requires_consent_and_creates_integrity_snapshot():
 _,_,c=setup_open();x=runtime.applications.create('no-consent',c.id,given_names='A',family_name='B');runtime.applications.upload('no-consent',x.id,'DIPLOME','d.pdf','application/pdf',b'%PDF-1.4\nx')
 with pytest.raises(ValueError,match='consents_required'):runtime.applications.submit('no-consent',x.id,1)
 consent('no-consent',x.id);runtime.applications.submit('no-consent',x.id,1);snap=runtime.application_repo.snapshot(x.id);assert len(snap.payload_sha256)==64 and len(snap.document_manifest_sha256)==64

def test_phase3_candidate_can_withdraw_and_delete_draft_document():
 _,_,c=setup_open();x=runtime.applications.create('withdraw',c.id,given_names='A',family_name='B');d=runtime.applications.upload('withdraw',x.id,'DIPLOME','d.pdf','application/pdf',b'%PDF-1.4\nx');runtime.applications.delete_document('withdraw',x.id,d.id);assert not runtime.applications.readiness('withdraw',x.id)['ready'];y=runtime.applications.withdraw('withdraw',x.id,x.row_version);assert y.state.value=='withdrawn'

def test_phase4_intake_is_idempotent_and_tenant_isolated():
 admin,inst,x,_=submitted();r=runtime.admission_center.intake(admin,inst.id,x.id);assert runtime.admission_center.intake(admin,inst.id,x.id).id==r.id
 other,otherinst,_=setup_open()
 with pytest.raises(ValueError):runtime.admission_center.intake(other,otherinst.id,x.id)

def test_phase4_document_verification_correction_and_readmission_to_review():
 admin,inst,x,d=submitted('corr');r=runtime.admission_center.intake(admin,inst.id,x.id);r=runtime.admission_center.assign(admin,inst.id,r.id,'reviewer-1',r.row_version);runtime.admission_center.review_document(admin,inst.id,r.id,d.id,'correction_required','scan illisible');r=runtime.admission_center.request_correction(admin,inst.id,r.id,r.row_version,'Remplacer le scan');app=runtime.application_repo.get(x.id);assert app.state.value=='draft' and r.state.value=='correction_required'

def test_phase4_requires_all_active_documents_accepted_before_complete():
 admin,inst,x,d=submitted('verify');r=runtime.admission_center.intake(admin,inst.id,x.id)
 with pytest.raises(ValueError,match='not_all_accepted'):runtime.admission_center.mark_complete(admin,inst.id,r.id,r.row_version)
 runtime.admission_center.review_document(admin,inst.id,r.id,d.id,'accepted');r=runtime.admission_center.mark_complete(admin,inst.id,r.id,r.row_version);assert r.state.value=='complete'

def test_phase4_decision_requires_privilege_and_refusal_reason():
 admin,inst,x,d=submitted('decision');r=runtime.admission_center.intake(admin,inst.id,x.id);runtime.admission_center.review_document(admin,inst.id,r.id,d.id,'accepted');r=runtime.admission_center.mark_complete(admin,inst.id,r.id,r.row_version)
 with pytest.raises(ValueError,match='refusal_reason'):runtime.admission_center.decide(admin,inst.id,r.id,r.row_version,'refused')
 r=runtime.admission_center.decide(admin,inst.id,r.id,r.row_version,'admitted');assert r.state.value=='admitted' and r.decided_at

def test_phase4_faculty_admin_cannot_take_final_decision():
 admin,inst,x,d=submitted('leastpriv');faculty=next(u for u in runtime.campus_repo.list_units(inst.id) if u.kind.value=='faculty');runtime.campus.invite_member(admin,inst.id,account_id='faculty-reviewer',role=CampusRole.FACULTY_ADMIN,unit_id=faculty.id);runtime.campus.accept_invitation('faculty-reviewer',inst.id);r=runtime.admission_center.intake(admin,inst.id,x.id);runtime.admission_center.review_document(admin,inst.id,r.id,d.id,'accepted');r=runtime.admission_center.mark_complete(admin,inst.id,r.id,r.row_version)
 with pytest.raises(PermissionError):runtime.admission_center.decide('faculty-reviewer',inst.id,r.id,r.row_version,'admitted')
