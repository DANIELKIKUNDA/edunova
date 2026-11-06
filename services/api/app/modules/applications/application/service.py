from dataclasses import replace
from hashlib import sha256
import json,re
from uuid import uuid4
from datetime import timedelta
from pathlib import PurePath
from app.modules.applications.domain.model import *
class ApplicationService:
 ALLOWED_TYPES={'application/pdf','image/jpeg','image/png','image/webp'}
 MAX_BYTES=12*1024*1024
 def __init__(self,repo,catalog_repo,campus_repo,storage,now,audit=None,scanner=None):self.repo=repo;self.catalog_repo=catalog_repo;self.campus_repo=campus_repo;self.storage=storage;self.now=now;self.audit=audit;self.scanner=scanner
 def get(self,aid):return self.repo.get(aid)
 def documents(self,aid):return self.repo.documents(aid)
 def _owned(self,account,aid):
  x=self.repo.get(aid)
  if not x or x.account_id!=account:raise ValueError('application_not_found')
  return x
 def _audit(self,a,action,x,meta=None):
  if self.audit:self.audit.write(actor_id=a,action=action,entity_type='candidate_application',entity_id=x,metadata=meta or {})
 def create(self,account,campaign_id,**profile):
  c=self.catalog_repo.campaign_any(campaign_id)
  if not c:raise ValueError('application_campaign_not_found')
  n=self.now()
  if c.state.value!='published' or n<c.opens_at or n>=c.closes_at:raise ValueError('application_campaign_not_open')
  old=self.repo.by_account_campaign(account,campaign_id)
  if old:return old
  gn=(profile.get('given_names') or '').strip();fn=(profile.get('family_name') or '').strip()
  if not gn or not fn:raise ValueError('application_name_required')
  x=CandidateApplication(uuid4().hex,account,c.institution_id,c.id,ApplicationState.DRAFT,gn,fn,profile.get('birth_date'),profile.get('nationality_code'),profile.get('gender'),profile.get('address'),profile.get('city'),profile.get('country_code'),profile.get('phone_number'),profile.get('email'),1,n,n)
  self.repo.save(x);self._audit(account,'application.created',x.id);return x
 def update(self,account,aid,expected_version,**changes):
  x=self._owned(account,aid)
  if x.state!=ApplicationState.DRAFT:raise ValueError('application_not_editable')
  if x.row_version!=expected_version:raise ValueError('application_concurrent_modification')
  allowed={'given_names','family_name','birth_date','nationality_code','gender','address','city','country_code','phone_number','email'}
  changes={k:v for k,v in changes.items() if k in allowed}
  y=replace(x,**changes,row_version=x.row_version+1,updated_at=self.now())
  if not y.given_names.strip() or not y.family_name.strip():raise ValueError('application_name_required')
  self.repo.save(y,x.row_version);self._audit(account,'application.updated',aid);return y
 def upload(self,account,aid,requirement_code,filename,content_type,payload):
  x=self._owned(account,aid)
  if x.state!=ApplicationState.DRAFT:raise ValueError('application_not_editable')
  rs={r.code:r for r in self.catalog_repo.requirements(x.campaign_id)}
  if requirement_code not in rs or not rs[requirement_code].document_required:raise ValueError('application_invalid_document_requirement')
  if content_type not in self.ALLOWED_TYPES:raise ValueError('application_document_type_not_allowed')
  if not payload or len(payload)>self.MAX_BYTES:raise ValueError('application_document_size_invalid')
  # Do not trust the browser MIME declaration alone.
  signatures={'application/pdf':payload.startswith(b'%PDF-'),'image/jpeg':payload.startswith(b'\xff\xd8\xff'),'image/png':payload.startswith(b'\x89PNG\r\n\x1a\n'),'image/webp':len(payload)>=12 and payload[:4]==b'RIFF' and payload[8:12]==b'WEBP'}
  if not signatures.get(content_type,False):raise ValueError('application_document_signature_mismatch')
  safe=PurePath(filename).name[:180] or 'document';digest=sha256(payload).hexdigest()
  for z in self.repo.documents(x.id):
   if z.requirement_code==requirement_code and z.sha256==digest and z.state==DocumentState.UPLOADED:return z
  if self.scanner:self.scanner.scan(payload,filename=safe)
  did=uuid4().hex;key=f'applications/{x.institution_id}/{x.id}/{did}-{safe}'
  self.storage.put(key,payload,content_type=content_type)
  d=ApplicationDocument(did,x.id,requirement_code,safe,content_type,len(payload),digest,key,DocumentState.UPLOADED,self.now())
  current=[z for z in self.repo.documents(x.id) if z.requirement_code==requirement_code and z.state==DocumentState.UPLOADED]
  self.repo.add_document(d)
  for z in current:self.repo.mark_replaced(z.id,d.id)
  self._audit(account,'application.document.uploaded',aid,{'requirement_code':requirement_code,'sha256':digest,'size_bytes':len(payload)});return d
 def readiness(self,account,aid):
  x=self._owned(account,aid);rs=self.catalog_repo.requirements(x.campaign_id);docs=self.repo.documents(aid);active={d.requirement_code for d in docs if d.state==DocumentState.UPLOADED};missing=[]
  if not x.given_names.strip() or not x.family_name.strip():missing.append('identity')
  for r in rs:
   if r.required and r.document_required and r.code not in active:missing.append(r.code)
  return {'application_id':aid,'ready':not missing,'missing':missing,'documents':len(active)}
 def accept_consent(self,account,aid,kind,policy_version,evidence):
  x=self._owned(account,aid)
  if x.state!=ApplicationState.DRAFT:raise ValueError('application_not_editable')
  k=ConsentKind(kind);pv=policy_version.strip()
  if not pv:raise ValueError('application_policy_version_required')
  c=ApplicationConsent(uuid4().hex,aid,k,pv,self.now(),sha256(evidence.encode()).hexdigest());self.repo.add_consent(c);self._audit(account,'application.consent.accepted',aid,{'kind':k.value,'policy_version':pv});return c
 def list_mine(self,account):return self.repo.list_by_account(account)
 def delete_document(self,account,aid,did):
  x=self._owned(account,aid)
  if x.state!=ApplicationState.DRAFT:raise ValueError('application_not_editable')
  d=next((z for z in self.repo.documents(aid) if z.id==did and z.state==DocumentState.UPLOADED),None)
  if not d:raise ValueError('application_document_not_found')
  self.repo.delete_document(did);self.storage.delete(d.storage_key);self._audit(account,'application.document.deleted',aid,{'document_id':did})
 def reopen_for_correction(self,aid):
  x=self.repo.get(aid)
  if not x or x.state!=ApplicationState.SUBMITTED:raise ValueError('application_not_submitted')
  y=replace(x,state=ApplicationState.DRAFT,row_version=x.row_version+1,updated_at=self.now(),submitted_at=None);self.repo.save(y,x.row_version);return y
 def withdraw(self,account,aid,expected_version):
  x=self._owned(account,aid)
  if x.row_version!=expected_version:raise ValueError('application_concurrent_modification')
  if x.state not in {ApplicationState.DRAFT,ApplicationState.SUBMITTED}:raise ValueError('application_not_withdrawable')
  n=self.now();y=replace(x,state=ApplicationState.WITHDRAWN,row_version=x.row_version+1,updated_at=n,withdrawn_at=n);self.repo.save(y,x.row_version);self._audit(account,'application.withdrawn',aid);return y
 def submit(self,account,aid,expected_version):
  x=self._owned(account,aid)
  if x.state!=ApplicationState.DRAFT:raise ValueError('application_not_draft')
  if x.row_version!=expected_version:raise ValueError('application_concurrent_modification')
  c=self.catalog_repo.campaign(x.institution_id,x.campaign_id);n=self.now()
  if not c or c.state.value!='published' or n<c.opens_at or n>=c.closes_at:raise ValueError('application_campaign_not_open')
  if not self.readiness(account,aid)['ready']:raise ValueError('application_incomplete')
  cons={z.kind for z in self.repo.consents(aid)}
  if {ConsentKind.PRIVACY,ConsentKind.APPLICATION_DECLARATION}-cons:raise ValueError('application_consents_required')
  docs=sorted((d.requirement_code,d.sha256,d.size_bytes) for d in self.repo.documents(aid) if d.state==DocumentState.UPLOADED)
  payload=repr((x.given_names,x.family_name,x.birth_date,x.nationality_code,x.gender,x.address,x.city,x.country_code,x.phone_number,x.email)).encode();manifest=json.dumps(docs,separators=(',',':')).encode()
  snap=SubmissionSnapshot(uuid4().hex,aid,x.row_version,sha256(payload).hexdigest(),sha256(manifest).hexdigest(),n);self.repo.add_snapshot(snap)
  y=replace(x,state=ApplicationState.SUBMITTED,row_version=x.row_version+1,updated_at=n,submitted_at=n);self.repo.save(y,x.row_version);self._audit(account,'application.submitted',aid);return y
 def detail(self,account,aid):return self._owned(account,aid),self.repo.documents(aid),self.readiness(account,aid)

 def begin_upload(self,account,aid,requirement_code,filename,content_type,total_bytes,total_chunks,expected_sha256=None):
  x=self._owned(account,aid)
  if x.state!=ApplicationState.DRAFT:raise ValueError('application_not_editable')
  rs={r.code:r for r in self.catalog_repo.requirements(x.campaign_id)}
  if requirement_code not in rs or not rs[requirement_code].document_required:raise ValueError('application_invalid_document_requirement')
  if content_type not in self.ALLOWED_TYPES:raise ValueError('application_document_type_not_allowed')
  if total_bytes<1 or total_bytes>self.MAX_BYTES or total_chunks<1 or total_chunks>64:raise ValueError('application_upload_shape_invalid')
  if expected_sha256 and (len(expected_sha256)!=64 or any(c not in '0123456789abcdef' for c in expected_sha256.lower())):raise ValueError('application_upload_digest_invalid')
  n=self.now();u=UploadSession(uuid4().hex,aid,requirement_code,PurePath(filename).name[:180] or 'document',content_type,total_bytes,total_chunks,expected_sha256.lower() if expected_sha256 else None,n,n+timedelta(hours=24));self.repo.create_upload(u);self._audit(account,'application.upload.started',aid,{'upload_id':u.id,'total_bytes':total_bytes});return u
 def upload_chunk(self,account,aid,uid,index,payload):
  self._owned(account,aid);u=self.repo.upload(uid)
  if not u or u.application_id!=aid:raise ValueError('application_upload_not_found')
  if u.completed_at:raise ValueError('application_upload_completed')
  if self.now()>=u.expires_at:raise ValueError('application_upload_expired')
  if index<0 or index>=u.total_chunks or not payload or len(payload)>1024*1024:raise ValueError('application_upload_chunk_invalid')
  digest=sha256(payload).hexdigest();self.storage.put(f'application-chunks/{uid}/{index:04d}',payload,content_type='application/octet-stream');self.repo.save_chunk(uid,index,len(payload),digest);return {'upload_id':uid,'chunk_index':index,'sha256':digest}
 def upload_status(self,account,aid,uid):
  self._owned(account,aid);u=self.repo.upload(uid)
  if not u or u.application_id!=aid:raise ValueError('application_upload_not_found')
  chunks=self.repo.chunks(uid);return {'upload_id':uid,'received_chunks':[x[0] for x in chunks],'received_bytes':sum(x[1] for x in chunks),'total_chunks':u.total_chunks,'total_bytes':u.total_bytes,'completed':u.completed_at is not None}
 def complete_resumable_upload(self,account,aid,uid):
  self._owned(account,aid);u=self.repo.upload(uid)
  if not u or u.application_id!=aid:raise ValueError('application_upload_not_found')
  if u.completed_at:raise ValueError('application_upload_completed')
  chunks=self.repo.chunks(uid)
  if len(chunks)!=u.total_chunks or [x[0] for x in chunks]!=list(range(u.total_chunks)):raise ValueError('application_upload_incomplete')
  payload=b''.join(self.storage.read(f'application-chunks/{uid}/{i:04d}') for i in range(u.total_chunks))
  if len(payload)!=u.total_bytes:raise ValueError('application_upload_size_mismatch')
  digest=sha256(payload).hexdigest()
  if u.expected_sha256 and digest!=u.expected_sha256:raise ValueError('application_upload_digest_mismatch')
  d=self.upload(account,aid,u.requirement_code,u.original_name,u.content_type,payload);self.repo.complete_upload(uid,self.now())
  for i in range(u.total_chunks):self.storage.delete(f'application-chunks/{uid}/{i:04d}')
  return d
