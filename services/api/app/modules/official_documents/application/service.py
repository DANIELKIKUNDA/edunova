import hashlib,secrets,json
from dataclasses import replace
from io import BytesIO
from uuid import uuid4
from reportlab.pdfgen.canvas import Canvas
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from app.modules.official_documents.domain.model import OfficialDocument,DocumentState,OfficialDocumentEvent,OfficialDocumentTemplate,TemplateState
from app.modules.service_desk.domain.model import RequestState,RequestKind
from app.modules.campus.domain.model import MembershipState
from app.modules.service_desk.application.service import STAFF
from app.modules.student_records.domain.model import RegistrationState,CourseRegistrationState,StudentState
from app.modules.jury.domain.model import JuryState,JuryDecision

class OfficialDocumentService:
 def __init__(self,repo,service_desk,campus,students,now,jury=None,audit=None,academic_delivery_repo=None):self.repo=repo;self.desk=service_desk;self.campus=campus;self.students=students;self.now=now;self.jury=jury;self.audit=audit;self.academic_delivery_repo=academic_delivery_repo
 def _staff(self,a,i):
  m=self.campus.membership(i,a)
  if not m or m.state!=MembershipState.ACTIVE or m.role not in STAFF:raise PermissionError('official_document_staff_required')
 def _audit(self,a,action,target,metadata=None):
  if self.audit:self.audit.record(actor_id=a,action=action,target_type='official_document',target_id=target,metadata=metadata or {})
 def _diploma_evidence(self,i,st):
  if not self.jury:raise ValueError('official_document_jury_unavailable')
  found=[]
  for session,outcome in self.jury.published_passes(i,st.id):
   if session.state==JuryState.PUBLISHED and outcome.decision==JuryDecision.PASS and outcome.credits_earned>=outcome.credits_required:
    found.append((session,outcome))
  if not found:raise ValueError('official_document_published_pass_jury_required')
  # Diploma issuance is based on the most recent published jury evidence, and a completed registration in that exact academic scope.
  found.sort(key=lambda x:(x[0].updated_at,x[0].id),reverse=True);session,outcome=found[0]
  regs=[r for r in self.students.registrations(st.id) if r.institution_id==i and r.academic_year_id==session.academic_year_id and r.curriculum_id==session.curriculum_id and r.cohort_id==session.cohort_id and r.state==RegistrationState.COMPLETED]
  if not regs:raise ValueError('official_document_completed_registration_required')
  return session,outcome
 def _transcript_lines(self,st):
  if not self.academic_delivery_repo:raise ValueError('official_document_transcript_provenance_unavailable')
  regs=sorted(self.students.registrations(st.id),key=lambda r:(r.academic_year_id,r.id))
  ids={r.id for r in regs if r.state in {RegistrationState.ENROLLED,RegistrationState.COMPLETED}}
  courses=sorted((c for c in self.students.course_registrations(st.id) if c.registration_id in ids and c.state in {CourseRegistrationState.VALIDATED,CourseRegistrationState.FAILED}),key=lambda c:(c.semester,c.course_code or '',c.course_title,c.id))
  if not courses:raise ValueError('official_document_transcript_results_missing')
  ledger={x.course_registration_id:x for x in self.academic_delivery_repo.published_results(st.institution_id,st.id)}
  missing=[c.id for c in courses if c.id not in ledger]
  if missing:raise ValueError('official_document_transcript_published_provenance_required')
  lines=[];proof=[]
  for c in courses:
   result=ledger[c.id]
   expected=CourseRegistrationState.VALIDATED if result.passed else CourseRegistrationState.FAILED
   if c.state!=expected:raise ValueError('official_document_transcript_state_provenance_mismatch')
   cr='' if c.credits is None else f'{c.credits:g}'
   outcome='REUSSI' if result.passed else 'ECHEC'
   lines.append(f'S{c.semester} | {c.course_code or "-"} | {c.course_title} | {cr} cr | {result.percent:.2f}% | {outcome}')
   proof.append({'course_registration_id':c.id,'curriculum_course_id':c.curriculum_course_id,'code':c.course_code,'title':c.course_title,'semester':c.semester,'credits':c.credits,'state':c.state.value,'gradebook_id':result.gradebook_id,'offering_id':result.offering_id,'percent':result.percent,'passed':result.passed,'result_evidence_hash':result.evidence_hash,'published_at':result.published_at.isoformat()})
  evidence=hashlib.sha256(json.dumps(proof,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  return lines,evidence
 def _issuer_snapshot(self,i):
  inst=self.campus.institution(i)
  if not inst:raise ValueError('official_document_institution_not_found')
  return inst.name,inst.legal_name or inst.name,inst.country_code
 def _render(self,i,st,kind,title,serial,token,extra,issuer_name=None,issuer_legal_name=None,issuer_country_code=None,template_version='official-v1'):
  out=BytesIO();c=Canvas(out,pagesize=(595,842));c.setTitle(title);c.setFont('Helvetica-Bold',16);c.drawString(55,790,'DOCUMENT INSTITUTIONNEL - EDUNOVA');c.setFont('Helvetica',10)
  base=[f'Universite: {issuer_name or i}',f'Denomination legale: {issuer_legal_name or issuer_name or i}',f'Pays: {issuer_country_code or ""}',f'Modele: {template_version}',f'Type: {kind}',f'Numero: {serial}',f'Matricule: {st.matricule}',f'Etudiant: {getattr(st,"given_names","")} {getattr(st,"family_name","")}'.strip(),f'Titre: {title}',f'Date: {self.now().date().isoformat()}']
  y=755
  for line in base:
   c.drawString(55,y,line[:105]);y-=20
  y-=8
  for line in extra:
   if y<100:c.showPage();c.setFont('Helvetica',9);y=790
   c.drawString(55,y,line[:115]);y-=17
  verify=f'/v1/official-documents/verify/{token}'
  c.setFont('Helvetica',8);c.drawString(55,62,'Verification: '+verify[:90])
  widget=qr.QrCodeWidget(verify);bounds=widget.getBounds();w=bounds[2]-bounds[0];h=bounds[3]-bounds[1];d=Drawing(58,58,transform=[58/w,0,0,58/h,0,0]);d.add(widget);renderPDF.draw(d,c,475,45)
  c.showPage();c.save();return out.getvalue()
 def issue(self,a,i,request_id,title,replaces_document_id=None):
  self._staff(a,i);req=self.desk.get(a,i,request_id)
  if req.state!=RequestState.APPROVED:raise ValueError('official_document_request_not_approved')
  supported=(RequestKind.ATTESTATION,RequestKind.TRANSCRIPT,RequestKind.DIPLOMA,RequestKind.CERTIFICATE,RequestKind.DUPLICATE,RequestKind.ADMIN_CORRECTION)
  if req.kind not in supported:raise ValueError('official_document_kind_not_supported')
  title=title.strip()
  if not 5<=len(title)<=200:raise ValueError('official_document_title_invalid')
  st=self.students.get(req.student_id)
  if not st or st.institution_id!=i:raise ValueError('official_document_student_invalid')
  if self.repo.by_request(i,request_id):raise ValueError('official_document_already_issued')
  source_hash=None;source_jury=None;extra=[];replacement_original=None
  if req.kind==RequestKind.DIPLOMA:
   session,outcome=self._diploma_evidence(i,st);source_hash=outcome.evidence_hash;source_jury=outcome.id
   extra=[f'Decision jury: {outcome.decision.value}',f'Credits acquis: {outcome.credits_earned:g}/{outcome.credits_required:g}',f'Annee academique: {session.academic_year_id}',f'Curriculum: {session.curriculum_id}',f'Preuve academique: {outcome.evidence_hash}']
  elif req.kind==RequestKind.TRANSCRIPT:
   extra,source_hash=self._transcript_lines(st)
  elif req.kind in {RequestKind.DUPLICATE,RequestKind.ADMIN_CORRECTION}:
   if not replaces_document_id:raise ValueError('official_document_duplicate_source_required')
   original=self.repo.get(i,replaces_document_id)
   if not original or original.student_id!=st.id:raise ValueError('official_document_duplicate_source_invalid')
   if req.kind==RequestKind.DUPLICATE and original.kind==RequestKind.DUPLICATE.value:raise ValueError('official_document_duplicate_chain_forbidden')
   if original.state!=DocumentState.ISSUED:raise ValueError('official_document_duplicate_original_not_active')
   source_hash=original.sha256_hex;replacement_original=original if req.kind==RequestKind.ADMIN_CORRECTION else None;extra=[f'Origine: {original.serial_number}',f'Empreinte original: {original.sha256_hex}']
  doc_id=uuid4().hex;token=secrets.token_urlsafe(32);serial=f'EDN-{i[:8].upper()}-{doc_id[:16].upper()}'
  issuer_name,issuer_legal_name,issuer_country_code=self._issuer_snapshot(i)
  effective_kind=replacement_original.kind if replacement_original else req.kind.value
  template=self.repo.active_template(i,effective_kind)
  if not template:raise ValueError('official_document_published_template_required')
  template_version=template.version
  pdf=self._render(i,st,req.kind.value,title,serial,token,extra,issuer_name,issuer_legal_name,issuer_country_code,template_version);digest=hashlib.sha256(pdf).hexdigest()
  doc=OfficialDocument(doc_id,i,req.student_id,request_id,serial,effective_kind,title,digest,pdf,hashlib.sha256(token.encode()).hexdigest(),DocumentState.ISSUED,a,self.now(),None,None,None,source_hash,source_jury,replaces_document_id,issuer_name,issuer_legal_name,issuer_country_code,template_version)
  from app.modules.service_desk.domain.model import RequestEvent
  fulfilled=replace(req,state=RequestState.FULFILLED,output_document_ref=doc_id,output_sha256=digest,version=req.version+1,updated_at=self.now());event=RequestEvent(uuid4().hex,req.id,a,'fulfilled',None,self.now())
  doc_event=OfficialDocumentEvent(uuid4().hex,i,doc.id,a,'issued',None,self.now())
  if replacement_original:
   self.repo.replace_with_fulfillment(doc,fulfilled,req.version,event,doc_event,replacement_original.id,a,'Remplace par document corrige '+doc.serial_number,self.now())
  else:self.repo.issue_with_fulfillment(doc,fulfilled,req.version,event,doc_event)
  self._audit(a,'official_document.issued',doc.id,{'kind':doc.kind,'serial':doc.serial_number,'source_evidence_hash':source_hash});return doc,token
 def create_template(self,a,i,kind,version,name):
  self._staff(a,i);kind=kind.strip();version=version.strip();name=name.strip()
  allowed={x.value for x in (RequestKind.ATTESTATION,RequestKind.TRANSCRIPT,RequestKind.DIPLOMA,RequestKind.CERTIFICATE)}
  if kind not in allowed:raise ValueError('official_document_template_kind_invalid')
  if not 1<=len(version)<=40 or not 3<=len(name)<=200:raise ValueError('official_document_template_invalid')
  t=OfficialDocumentTemplate(uuid4().hex,i,kind,version,name,TemplateState.DRAFT,a,self.now());self.repo.create_template(t);return t
 def publish_template(self,a,i,tid):
  self._staff(a,i);self.repo.publish_template(i,tid,a,self.now());self._audit(a,'official_document.template_published',tid)
 def get(self,a,i,d):
  doc=self.repo.get(i,d)
  if not doc:raise ValueError('official_document_not_found')
  st=self.students.get(doc.student_id)
  if not st or (a!=st.account_id and not self._authorized_staff(a,i)):raise PermissionError('official_document_access_denied')
  return doc
 def _authorized_staff(self,a,i):
  try:self._staff(a,i);return True
  except PermissionError:return False
 def revoke(self,a,i,d,reason):
  self._staff(a,i)
  reason=reason.strip()
  if not 5<=len(reason)<=1000:raise ValueError('official_document_revocation_reason_invalid')
  doc=self.repo.get(i,d)
  if not doc:raise ValueError('official_document_not_found')
  event=OfficialDocumentEvent(uuid4().hex,i,d,a,'revoked',reason,self.now())
  self.repo.revoke(i,d,a,reason,self.now(),event);self._audit(a,'official_document.revoked',d,{'reason':reason.strip()})
 def history(self,a,i,d):
  self._staff(a,i)
  if not self.repo.get(i,d):raise ValueError('official_document_not_found')
  return self.repo.events(i,d)
 def verify(self,token):
  if len(token)<32:return {'valid':False,'status':'unknown'}
  doc=self.repo.by_token_hash(hashlib.sha256(token.encode()).hexdigest())
  if not doc:return {'valid':False,'status':'unknown'}
  return {'valid':doc.state==DocumentState.ISSUED,'status':doc.state.value,'serial_number':doc.serial_number,'document_type':doc.kind,'sha256':doc.sha256_hex,'issued_at':doc.issued_at.isoformat(),'replaces_document_id':doc.replaces_document_id,'issuer_name':doc.issuer_name,'issuer_legal_name':doc.issuer_legal_name,'issuer_country_code':doc.issuer_country_code,'template_version':doc.template_version}
