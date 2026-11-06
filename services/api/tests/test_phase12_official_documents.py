from datetime import datetime,timezone
from types import SimpleNamespace as O
from unittest.mock import Mock
from dataclasses import replace
import hashlib,pytest
from app.modules.official_documents.application.service import OfficialDocumentService
from app.modules.official_documents.domain.model import DocumentState,OfficialDocumentTemplate,TemplateState
from app.modules.service_desk.domain.model import RequestKind,RequestState,ServiceRequest
from app.modules.campus.domain.model import CampusRole,MembershipState
NOW=lambda:datetime(2026,10,9,tzinfo=timezone.utc)
def fx():
 r=Mock();d=Mock();c=Mock();s=Mock()
 c.membership.side_effect=lambda i,a:O(role=CampusRole.RECTOR if a=='rector' else CampusRole.STUDENT,state=MembershipState.ACTIVE)
 c.institution.return_value=O(id='univ',name='Universite Exemple',legal_name='Universite Exemple ASBL',country_code='CD')
 st=O(id='student-record',institution_id='univ',account_id='student',matricule='EDN-123');s.get.return_value=st
 req=ServiceRequest('req','univ','student-record','student',RequestKind.ATTESTATION,'Attestation','',RequestState.APPROVED,None,None,None,None,3,NOW(),NOW())
 d.get.return_value=req;r.by_request.return_value=None
 r.active_template.return_value=OfficialDocumentTemplate('tpl','univ','attestation','2026.1','Modele officiel',TemplateState.PUBLISHED,'rector',NOW(),'rector',NOW())
 return OfficialDocumentService(r,d,c,s,NOW),r,d,req

def test_issue_produces_actual_pdf_and_atomic_request_fulfillment():
 svc,r,_,_=fx();doc,token=svc.issue('rector','univ','req','Attestation de scolarite')
 assert doc.pdf_bytes.startswith(b'%PDF-') and hashlib.sha256(doc.pdf_bytes).hexdigest()==doc.sha256_hex
 assert doc.verification_token_hash==hashlib.sha256(token.encode()).hexdigest()
 saved,request,version,event,doc_event=r.issue_with_fulfillment.call_args.args
 assert request.state==RequestState.FULFILLED and request.output_document_ref==doc.id and version==3 and event.event_type=='fulfilled'
 assert doc_event.event_type=='issued' and doc_event.document_id==doc.id
 r.by_token_hash.return_value=doc
 assert svc.verify(token)['valid']
 assert 'student-record' not in str(svc.verify(token))

def test_no_issue_without_approved_request():
 svc,r,d,req=fx();d.get.return_value=replace(req,state=RequestState.SUBMITTED) if hasattr(req,'__dataclass_fields__') else O(**{**vars(req),'state':RequestState.SUBMITTED})
 with pytest.raises(ValueError,match='not_approved'):svc.issue('rector','univ','req','Attestation de scolarite')
 r.issue_with_fulfillment.assert_not_called()

def test_student_cannot_issue_or_revoke():
 svc,r,_,_=fx()
 with pytest.raises(PermissionError):svc.issue('student','univ','req','Attestation de scolarite')
 with pytest.raises(PermissionError):svc.revoke('student','univ','doc','raison')

def test_verification_revoked_is_not_valid():
 svc,r,_,_=fx();doc,token=svc.issue('rector','univ','req','Attestation de scolarite')
 r.by_token_hash.return_value=replace(doc,state=DocumentState.REVOKED)
 assert svc.verify(token)['valid'] is False
 assert svc.verify('invalid')=={'valid':False,'status':'unknown'}

def test_no_duplicate_issuance():
 svc,r,_,_=fx();r.by_request.return_value=O(id='previous')
 with pytest.raises(ValueError,match='already_issued'):svc.issue('rector','univ','req','Attestation de scolarite')

def test_diploma_requires_published_pass_and_completed_registration():
 from app.modules.jury.domain.model import JuryState,JuryDecision
 from app.modules.student_records.domain.model import RegistrationState
 svc,r,d,req=fx();jury=Mock();svc.jury=jury
 d.get.return_value=replace(req,kind=RequestKind.DIPLOMA)
 session=O(id='js',state=JuryState.PUBLISHED,updated_at=NOW(),academic_year_id='2025',curriculum_id='cur',cohort_id='coh')
 outcome=O(id='out',decision=JuryDecision.PASS,credits_earned=180.0,credits_required=180.0,evidence_hash='a'*64)
 jury.published_passes.return_value=((session,outcome),)
 svc.students.registrations.return_value=[O(id='reg',institution_id='univ',academic_year_id='2025',curriculum_id='cur',cohort_id='coh',state=RegistrationState.COMPLETED)]
 doc,token=svc.issue('rector','univ','req','Diplome officiel')
 assert doc.kind=='diploma' and doc.source_jury_outcome_id=='out' and doc.source_evidence_hash=='a'*64
 assert doc.pdf_bytes.startswith(b'%PDF-') and len(token)>=32

def test_diploma_refuses_without_published_jury_pass():
 svc,r,d,req=fx();jury=Mock();svc.jury=jury;d.get.return_value=replace(req,kind=RequestKind.DIPLOMA);jury.published_passes.return_value=()
 with pytest.raises(ValueError,match='published_pass_jury_required'):svc.issue('rector','univ','req','Diplome officiel')
 r.issue_with_fulfillment.assert_not_called()

def test_transcript_is_derived_from_canonical_course_registrations():
 from app.modules.student_records.domain.model import RegistrationState,CourseRegistrationState
 svc,r,d,req=fx();d.get.return_value=replace(req,kind=RequestKind.TRANSCRIPT)
 svc.students.registrations.return_value=[O(id='reg',state=RegistrationState.COMPLETED,academic_year_id='2025')]
 svc.students.course_registrations.return_value=[O(id='c1',registration_id='reg',curriculum_course_id='ecue1',semester=1,course_code='MAT101',course_title='Mathematiques',credits=6.0,state=CourseRegistrationState.VALIDATED)]
 delivery=Mock();delivery.published_results.return_value=[O(course_registration_id='c1',gradebook_id='gb1',offering_id='off1',percent=78.5,passed=True,evidence_hash='b'*64,published_at=NOW())];svc.academic_delivery_repo=delivery
 doc,_=svc.issue('rector','univ','req','Releve academique officiel')
 assert doc.source_evidence_hash and len(doc.source_evidence_hash)==64 and doc.kind=='transcript'
 lines,_=svc._transcript_lines(svc.students.get.return_value);assert '78.50%' in lines[0]

def test_duplicate_requires_original_document_same_student():
 svc,r,d,req=fx();d.get.return_value=replace(req,kind=RequestKind.DUPLICATE)
 with pytest.raises(ValueError,match='duplicate_source_required'):svc.issue('rector','univ','req','Duplicata officiel')
 original=O(id='orig',student_id='other') ; r.get.return_value=original
 with pytest.raises(ValueError,match='duplicate_source_invalid'):svc.issue('rector','univ','req','Duplicata officiel','orig')


def test_transcript_refuses_legacy_state_without_published_grade_provenance():
 from app.modules.student_records.domain.model import RegistrationState,CourseRegistrationState
 svc,r,d,req=fx();d.get.return_value=replace(req,kind=RequestKind.TRANSCRIPT)
 svc.students.registrations.return_value=[O(id='reg',state=RegistrationState.COMPLETED,academic_year_id='2025')]
 svc.students.course_registrations.return_value=[O(id='c1',registration_id='reg',curriculum_course_id='ecue1',semester=1,course_code='MAT101',course_title='Mathematiques',credits=6.0,state=CourseRegistrationState.VALIDATED)]
 delivery=Mock();delivery.published_results.return_value=[];svc.academic_delivery_repo=delivery
 with pytest.raises(ValueError,match='published_provenance_required'):svc.issue('rector','univ','req','Releve academique officiel')
 r.issue_with_fulfillment.assert_not_called()


def test_official_document_orm_persists_all_provenance_fields():
 from app.modules.official_documents.infrastructure.sqlalchemy_repo import OfficialDocumentRow
 from sqlalchemy import inspect
 cols={c.key for c in inspect(OfficialDocumentRow).columns}
 assert {'source_evidence_hash','source_jury_outcome_id','replaces_document_id'}<=cols

def test_duplicate_rejects_revoked_original_and_duplicate_chain():
 svc,r,d,req=fx();d.get.return_value=replace(req,kind=RequestKind.DUPLICATE)
 original=O(id='orig',student_id='student-record',kind=RequestKind.ATTESTATION.value,state=DocumentState.REVOKED,sha256_hex='a'*64)
 r.get.return_value=original
 with pytest.raises(ValueError,match='original_not_active'):svc.issue('rector','univ','req','Duplicata officiel','orig')
 original.state=DocumentState.ISSUED;original.kind=RequestKind.DUPLICATE.value
 with pytest.raises(ValueError,match='chain_forbidden'):svc.issue('rector','univ','req','Duplicata officiel','orig')


def test_document_snapshots_issuer_identity_and_template_version():
 svc,r,_,_=fx();doc,token=svc.issue('rector','univ','req','Attestation de scolarite')
 assert doc.issuer_name=='Universite Exemple' and doc.issuer_legal_name=='Universite Exemple ASBL'
 assert doc.issuer_country_code=='CD' and doc.template_version=='2026.1'
 r.by_token_hash.return_value=doc;v=svc.verify(token)
 assert v['issuer_name']=='Universite Exemple' and v['template_version']=='2026.1'

def test_issuer_snapshot_is_immutable_after_institution_rename():
 svc,r,_,_=fx();doc,token=svc.issue('rector','univ','req','Attestation de scolarite')
 svc.campus.institution.return_value=O(id='univ',name='Nouveau Nom',legal_name='Nouveau Nom SARL',country_code='CD')
 r.by_token_hash.return_value=doc
 assert svc.verify(token)['issuer_name']=='Universite Exemple'


def test_revocation_is_atomic_with_lifecycle_event_and_reason_validation():
 svc,r,_,_=fx();r.get.return_value=O(id='doc',institution_id='univ')
 with pytest.raises(ValueError,match='reason_invalid'):svc.revoke('rector','univ','doc','x')
 r.revoke.assert_not_called()
 svc.revoke('rector','univ','doc','Erreur administrative constatee')
 args=r.revoke.call_args.args
 assert args[0:3]==('univ','doc','rector') and args[3]=='Erreur administrative constatee'
 assert args[5].event_type=='revoked' and args[5].document_id=='doc'

def test_document_history_is_staff_only_and_tenant_scoped():
 svc,r,_,_=fx();r.get.return_value=O(id='doc');r.events.return_value=[]
 assert svc.history('rector','univ','doc')==[]
 r.events.assert_called_once_with('univ','doc')
 with pytest.raises(PermissionError):svc.history('student','univ','doc')


def test_issuance_requires_published_institutional_template():
 svc,r,_,_=fx();r.active_template.return_value=None
 with pytest.raises(ValueError,match='published_template_required'):svc.issue('rector','univ','req','Attestation de scolarite')
 r.issue_with_fulfillment.assert_not_called()

def test_template_governance_create_and_publish():
 svc,r,_,_=fx();t=svc.create_template('rector','univ','diploma','2026.2','Diplome officiel 2026')
 assert t.state==TemplateState.DRAFT and t.version=='2026.2'
 svc.publish_template('rector','univ',t.id);r.publish_template.assert_called_once()
 with pytest.raises(PermissionError):svc.create_template('student','univ','diploma','x','Modele')

def test_admin_correction_atomically_supersedes_original():
 svc,r,d,req=fx();d.get.return_value=replace(req,kind=RequestKind.ADMIN_CORRECTION)
 original=O(id='orig',student_id='student-record',kind=RequestKind.ATTESTATION.value,state=DocumentState.ISSUED,sha256_hex='a'*64,serial_number='EDN-OLD')
 r.get.return_value=original
 doc,_=svc.issue('rector','univ','req','Attestation corrigee','orig')
 assert doc.kind==RequestKind.ATTESTATION.value and doc.replaces_document_id=='orig'
 assert r.replace_with_fulfillment.call_count==1 and r.issue_with_fulfillment.call_count==0
