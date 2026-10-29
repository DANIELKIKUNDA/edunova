from dataclasses import replace
from uuid import uuid4
from app.modules.admissions_center.domain.model import *
from app.modules.applications.domain.model import ApplicationState,DocumentState
from app.modules.campus.domain.model import CampusRole
WRITE={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN,CampusRole.FACULTY_ADMIN}
DECIDE={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN}
class AdmissionCenterService:
 def __init__(self,repo,apps,campus,now,audit=None):self.repo=repo;self.apps=apps;self.campus=campus;self.now=now;self.audit=audit
 def _auth(self,a,i,roles=WRITE):return self.campus.membership(a,i,roles)
 def _audit(self,a,action,id,meta=None):
  if self.audit:self.audit.write(actor_id=a,action=action,entity_type='admission_review',entity_id=id,metadata=meta or {})
 def intake(self,a,i,aid):
  self._auth(a,i);app=self.apps.get(aid)
  if not app or app.institution_id!=i:raise ValueError('admission_application_not_found')
  if app.state!=ApplicationState.SUBMITTED:raise ValueError('admission_application_not_submitted')
  old=self.repo.by_application(aid)
  if old:return old
  n=self.now();x=AdmissionReview(uuid4().hex,aid,i,ReviewState.PENDING,None,None,1,n,n);self.repo.save(x);self._audit(a,'admission.review.intake',x.id);return x
 def list(self,a,i,state=None):self._auth(a,i);return self.repo.list(i,state)
 def assign(self,a,i,rid,assignee,expected):
  self._auth(a,i);x=self.repo.get(rid)
  if not x or x.institution_id!=i:raise ValueError('admission_review_not_found')
  if x.row_version!=expected:raise ValueError('admission_review_concurrent_modification')
  y=replace(x,assigned_to=assignee,state=ReviewState.IN_REVIEW if x.state==ReviewState.PENDING else x.state,row_version=x.row_version+1,updated_at=self.now());self.repo.save(y,x.row_version);self._audit(a,'admission.review.assigned',rid,{'assignee':assignee});return y
 def review_document(self,a,i,rid,did,state,note=None):
  self._auth(a,i);x=self.repo.get(rid)
  if not x or x.institution_id!=i:raise ValueError('admission_review_not_found')
  docs={d.id:d for d in self.apps.documents(x.application_id)}
  if did not in docs or docs[did].state!=DocumentState.UPLOADED:raise ValueError('admission_document_not_active')
  st=DocumentReviewState(state);r=DocumentReview(uuid4().hex,rid,did,st,note.strip() if note else None,a,self.now());self.repo.save_doc_review(r);self._audit(a,'admission.document.reviewed',rid,{'document_id':did,'state':st.value});return r
 def mark_complete(self,a,i,rid,expected):
  self._auth(a,i);x=self.repo.get(rid)
  if not x or x.institution_id!=i:raise ValueError('admission_review_not_found')
  if x.row_version!=expected:raise ValueError('admission_review_concurrent_modification')
  active=[d for d in self.apps.documents(x.application_id) if d.state==DocumentState.UPLOADED];reviews={r.document_id:r for r in self.repo.doc_reviews(rid)}
  if any(d.id not in reviews or reviews[d.id].state!=DocumentReviewState.ACCEPTED for d in active):raise ValueError('admission_documents_not_all_accepted')
  y=replace(x,state=ReviewState.COMPLETE,row_version=x.row_version+1,updated_at=self.now());self.repo.save(y,x.row_version);self._audit(a,'admission.review.complete',rid);return y
 def request_correction(self,a,i,rid,expected,reason):
  self._auth(a,i);x=self.repo.get(rid)
  if not x or x.institution_id!=i:raise ValueError('admission_review_not_found')
  if x.row_version!=expected:raise ValueError('admission_review_concurrent_modification')
  if not reason.strip():raise ValueError('admission_correction_reason_required')
  y=replace(x,state=ReviewState.CORRECTION_REQUIRED,decision_reason=reason.strip(),row_version=x.row_version+1,updated_at=self.now());self.repo.save(y,x.row_version);self.apps.reopen_for_correction(x.application_id);self._audit(a,'admission.correction.requested',rid);return y
 def decide(self,a,i,rid,expected,decision,reason=None):
  self._auth(a,i,DECIDE);x=self.repo.get(rid)
  if not x or x.institution_id!=i:raise ValueError('admission_review_not_found')
  if x.row_version!=expected:raise ValueError('admission_review_concurrent_modification')
  target=ReviewState(decision)
  if target not in {ReviewState.ELIGIBLE,ReviewState.ADMITTED,ReviewState.REFUSED,ReviewState.WAITLISTED}:raise ValueError('admission_invalid_decision')
  if target in {ReviewState.ADMITTED,ReviewState.REFUSED,ReviewState.WAITLISTED} and x.state not in {ReviewState.COMPLETE,ReviewState.ELIGIBLE,ReviewState.WAITLISTED}:raise ValueError('admission_review_not_decidable')
  if target==ReviewState.REFUSED and not (reason or '').strip():raise ValueError('admission_refusal_reason_required')
  n=self.now();y=replace(x,state=target,decision_reason=reason.strip() if reason else None,row_version=x.row_version+1,updated_at=n,decided_at=n if target in {ReviewState.ADMITTED,ReviewState.REFUSED,ReviewState.WAITLISTED} else None);self.repo.save(y,x.row_version);self._audit(a,'admission.review.decided',rid,{'decision':target.value});return y
 def candidate_status(self,account,aid):
  app=self.apps.get(aid)
  if not app or app.account_id!=account:raise ValueError('application_not_found')
  r=self.repo.by_application(aid);return {'application_id':aid,'status':r.state.value if r else ('submitted' if app.state==ApplicationState.SUBMITTED else app.state.value),'reason':r.decision_reason if r and r.state==ReviewState.CORRECTION_REQUIRED else None}

def _event(self,actor,x,event,old=None,note=None):
 self.repo.save_event(AdmissionEvent(uuid4().hex,x.id,actor,event,old.value if hasattr(old,'value') else old,x.state.value,note,self.now()))
def create_committee(self,a,i,campaign_id,name,chair,members,quorum):
 self._auth(a,i,DECIDE)
 if quorum<1:raise ValueError('admission_committee_invalid_quorum')
 uniq=list(dict.fromkeys([chair,*members]))
 if quorum>len(uniq):raise ValueError('admission_committee_quorum_exceeds_members')
 c=AdmissionCommittee(uuid4().hex,i,campaign_id,name.strip(),chair,quorum,True,self.now());self.repo.save_committee(c,[(x,True) for x in uniq]);return c
def vote(self,a,i,cid,rid,recommendation,note=None):
 c=self.repo.committee(cid);r=self.repo.get(rid)
 if not c or c.institution_id!=i or not r or r.institution_id!=i:raise ValueError('admission_committee_or_review_not_found')
 if a not in {m.account_id for m in self.repo.committee_members(cid) if m.voting}:raise PermissionError('admission_committee_member_required')
 if self.apps.get(r.application_id).campaign_id!=c.campaign_id:raise ValueError('admission_committee_campaign_mismatch')
 if r.state not in {ReviewState.COMPLETE,ReviewState.ELIGIBLE,ReviewState.WAITLISTED}:raise ValueError('admission_review_not_votable')
 rec=recommendation.lower()
 if rec not in {'admit','refuse','waitlist','abstain'}:raise ValueError('admission_invalid_recommendation')
 v=CommitteeVote(uuid4().hex,cid,rid,a,rec,note.strip() if note else None,self.now());self.repo.save_vote(v);return v
def committee_tally(self,a,i,cid,rid):
 self._auth(a,i);c=self.repo.committee(cid)
 if not c or c.institution_id!=i:raise ValueError('admission_committee_not_found')
 vs=self.repo.votes(cid,rid);counts={k:0 for k in ('admit','refuse','waitlist','abstain')}
 for v in vs:counts[v.recommendation]+=1
 return {'committee_id':cid,'review_id':rid,'quorum':c.quorum,'votes_cast':len(vs),'quorum_met':len(vs)>=c.quorum,'counts':counts}
def timeline(self,a,i,rid):
 self._auth(a,i);r=self.repo.get(rid)
 if not r or r.institution_id!=i:raise ValueError('admission_review_not_found')
 return self.repo.events(rid)
def dashboard(self,a,i):
 self._auth(a,i);rows=self.repo.list(i);states={s.value:0 for s in ReviewState}
 for r in rows:states[r.state.value]+=1
 return {'total':len(rows),'states':states,'unassigned':sum(1 for r in rows if not r.assigned_to and r.state not in {ReviewState.ADMITTED,ReviewState.REFUSED,ReviewState.WITHDRAWN})}
AdmissionCenterService._event=_event
AdmissionCenterService.create_committee=create_committee
AdmissionCenterService.vote=vote
AdmissionCenterService.committee_tally=committee_tally
AdmissionCenterService.timeline=timeline
AdmissionCenterService.dashboard=dashboard

_old_intake=AdmissionCenterService.intake
_old_assign=AdmissionCenterService.assign
_old_complete=AdmissionCenterService.mark_complete
_old_correction=AdmissionCenterService.request_correction
_old_decide=AdmissionCenterService.decide
def intake2(self,a,i,aid):
 old=self.repo.by_application(aid);x=_old_intake(self,a,i,aid)
 if not old:self._event(a,x,'intake')
 return x
def assign2(self,a,i,rid,assignee,expected):
 old=self.repo.get(rid);x=_old_assign(self,a,i,rid,assignee,expected);self._event(a,x,'assigned',old.state,assignee);return x
def complete2(self,a,i,rid,expected):
 old=self.repo.get(rid);x=_old_complete(self,a,i,rid,expected);self._event(a,x,'completed',old.state);return x
def correction2(self,a,i,rid,expected,reason):
 old=self.repo.get(rid);x=_old_correction(self,a,i,rid,expected,reason);self._event(a,x,'correction_requested',old.state,reason);return x
def decide2(self,a,i,rid,expected,decision,reason=None):
 old=self.repo.get(rid);target=ReviewState(decision)
 if target==ReviewState.ADMITTED:
  app=self.apps.get(old.application_id);campaign=self.catalog.campaign_any(app.campaign_id) if getattr(self,'catalog',None) else None
  if campaign and campaign.capacity is not None and self.repo.count_state_for_campaign(app.campaign_id,ReviewState.ADMITTED,self.apps)>=campaign.capacity:raise ValueError('admission_campaign_capacity_reached')
 x=_old_decide(self,a,i,rid,expected,decision,reason);self._event(a,x,'decision',old.state,reason);return x
AdmissionCenterService.intake=intake2
AdmissionCenterService.assign=assign2
AdmissionCenterService.mark_complete=complete2
AdmissionCenterService.request_correction=correction2
AdmissionCenterService.decide=decide2
