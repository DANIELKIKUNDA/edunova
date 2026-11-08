from datetime import UTC,date,datetime,timedelta
import pytest, uuid
from app.runtime import runtime
from app.modules.campus.domain.model import UnitKind,PeriodKind

def setup_open():
 u=uuid.uuid4().hex;a='inst-'+u;i=runtime.campus.create_institution(a,name='Université '+u[:5],slug='cand-'+u);f=runtime.campus.add_unit(a,i.id,kind=UnitKind.FACULTY,name='Médecine',code='F'+u[:7]);p=runtime.campus.add_unit(a,i.id,kind=UnitKind.PROGRAM,name='Médecine',code='P'+u[:7],parent_id=f.id);y=runtime.campus.add_period(a,i.id,kind=PeriodKind.ACADEMIC_YEAR,name='2027-2028',starts_on=date(2027,9,1),ends_on=date(2028,7,31));cur=runtime.academic_catalog.create(a,i.id,program_unit_id=p.id,effective_academic_year_id=y.id,code='MED',title='Médecine');runtime.academic_catalog.import_medicine(a,i.id,cur.id);cur=runtime.academic_catalog.publish(a,i.id,cur.id,1);n=datetime.now(UTC);c=runtime.admissions_catalog.create(a,i.id,program_unit_id=p.id,academic_year_id=y.id,curriculum_id=cur.id,slug='med-'+u,title='Admissions médecine',summary='',opens_at=n-timedelta(days=1),closes_at=n+timedelta(days=30));runtime.admissions_catalog.add_requirement(a,i.id,c.id,code='DIPLOME',label='Diplôme',required=True,document_required=True);c=runtime.admissions_catalog.publish(a,i.id,c.id,1);return a,i,c

def consent(account,aid):
 runtime.applications.accept_consent(account,aid,'privacy','2026-10','privacy')
 runtime.applications.accept_consent(account,aid,'application_declaration','2026-10','declaration')

def test_candidate_draft_is_idempotent_per_campaign_and_private():
 _,_,c=setup_open();x=runtime.applications.create('candidate-a',c.id,given_names='Ada',family_name='Lovelace');same=runtime.applications.create('candidate-a',c.id,given_names='Other',family_name='Name');assert same.id==x.id
 with pytest.raises(ValueError,match='application_not_found'):runtime.applications.detail('candidate-b',x.id)

def test_required_document_blocks_submission_then_allows_it():
 _,_,c=setup_open();x=runtime.applications.create('candidate-doc',c.id,given_names='Marie',family_name='Curie');assert runtime.applications.readiness('candidate-doc',x.id)['ready'] is False
 with pytest.raises(ValueError,match='application_incomplete'):runtime.applications.submit('candidate-doc',x.id,1)
 pdf=b'%PDF-1.7\n% EduNova test document\n';d=runtime.applications.upload('candidate-doc',x.id,'DIPLOME','diplome.pdf','application/pdf',pdf);assert len(d.sha256)==64 and runtime.applications.readiness('candidate-doc',x.id)['ready'];consent('candidate-doc',x.id)
 y=runtime.applications.submit('candidate-doc',x.id,1);assert y.state.value=='submitted' and y.submitted_at

def test_document_signature_and_requirement_are_enforced():
 _,_,c=setup_open();x=runtime.applications.create('candidate-sec',c.id,given_names='K',family_name='N')
 with pytest.raises(ValueError,match='signature_mismatch'):runtime.applications.upload('candidate-sec',x.id,'DIPLOME','fake.pdf','application/pdf',b'not a pdf')
 with pytest.raises(ValueError,match='invalid_document_requirement'):runtime.applications.upload('candidate-sec',x.id,'PAS_DEMANDE','x.pdf','application/pdf',b'%PDF-1.4\n')

def test_same_document_upload_is_idempotent_and_replacement_is_versioned():
 _,_,c=setup_open();x=runtime.applications.create('candidate-replace',c.id,given_names='A',family_name='B');one=runtime.applications.upload('candidate-replace',x.id,'DIPLOME','one.pdf','application/pdf',b'%PDF-1.4\none');same=runtime.applications.upload('candidate-replace',x.id,'DIPLOME','one.pdf','application/pdf',b'%PDF-1.4\none');two=runtime.applications.upload('candidate-replace',x.id,'DIPLOME','two.pdf','application/pdf',b'%PDF-1.4\ntwo');docs=runtime.application_repo.documents(x.id);assert same.id==one.id and two.id!=one.id;assert sum(d.state.value=='uploaded' for d in docs)==1 and sum(d.state.value=='replaced' for d in docs)==1

def test_optimistic_lock_and_post_submission_immutability():
 _,_,c=setup_open();x=runtime.applications.create('candidate-lock',c.id,given_names='A',family_name='B');x=runtime.applications.update('candidate-lock',x.id,1,city='Lubumbashi')
 with pytest.raises(ValueError,match='concurrent_modification'):runtime.applications.update('candidate-lock',x.id,1,city='Kolwezi')
 runtime.applications.upload('candidate-lock',x.id,'DIPLOME','d.pdf','application/pdf',b'%PDF-1.4\nx');consent('candidate-lock',x.id);y=runtime.applications.submit('candidate-lock',x.id,x.row_version)
 with pytest.raises(ValueError,match='not_editable'):runtime.applications.update('candidate-lock',x.id,y.row_version,city='X')

def test_resumable_upload_survives_interruption_and_completes_in_order():
 _,_,c=setup_open();x=runtime.applications.create('candidate-resume',c.id,given_names='A',family_name='B');payload=b'%PDF-1.7\n'+b'x'*1200000;import hashlib
 u=runtime.applications.begin_upload('candidate-resume',x.id,'DIPLOME','large.pdf','application/pdf',len(payload),2,hashlib.sha256(payload).hexdigest());runtime.applications.upload_chunk('candidate-resume',x.id,u.id,0,payload[:800000]);st=runtime.applications.upload_status('candidate-resume',x.id,u.id);assert st['received_chunks']==[0] and not st['completed'];runtime.applications.upload_chunk('candidate-resume',x.id,u.id,1,payload[800000:]);d=runtime.applications.complete_resumable_upload('candidate-resume',x.id,u.id);assert d.sha256==hashlib.sha256(payload).hexdigest();assert runtime.applications.upload_status('candidate-resume',x.id,u.id)['completed']

def test_resumable_upload_rejects_digest_mismatch():
 _,_,c=setup_open();x=runtime.applications.create('candidate-digest',c.id,given_names='A',family_name='B');payload=b'%PDF-1.7\nhello';u=runtime.applications.begin_upload('candidate-digest',x.id,'DIPLOME','x.pdf','application/pdf',len(payload),1,'0'*64);runtime.applications.upload_chunk('candidate-digest',x.id,u.id,0,payload)
 with pytest.raises(ValueError,match='digest_mismatch'):runtime.applications.complete_resumable_upload('candidate-digest',x.id,u.id)
