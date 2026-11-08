from dataclasses import replace
from uuid import uuid4
from app.modules.campus.domain.model import CampusRole,MembershipState
from app.modules.teaching.domain.model import CourseState
from app.modules.assignments.domain.model import *
ADMIN={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN,CampusRole.FACULTY_ADMIN}
class AssignmentService:
 def __init__(self,repo,campus_repo,teaching_repo,now,audit=None):self.repo=repo;self.campus_repo=campus_repo;self.teaching_repo=teaching_repo;self.now=now;self.audit=audit
 def _audit(self,a,action,t,id,meta=None):
  if self.audit:self.audit.write(actor_id=a,action=action,entity_type=t,entity_id=id,metadata=meta or {})
 def _member(self,a,i):
  m=self.campus_repo.membership(i,a)
  if not m or m.state!=MembershipState.ACTIVE:raise PermissionError('assignment_membership_required')
  return m
 def _teacher(self,a,i,o):
  m=self._member(a,i);off=self.teaching_repo.offering(i,o)
  if not off:raise ValueError('assignment_offering_not_found')
  if m.role in ADMIN:return m
  ass=self.teaching_repo.assignment(o,a)
  if m.role==CampusRole.TEACHER and ass and ass.active:return m
  raise PermissionError('assignment_teacher_required')
 def _student_access(self,a,i,o):
  m=self._member(a,i)
  if m.role!=CampusRole.STUDENT:raise PermissionError('assignment_student_required')
  off=self.teaching_repo.offering(i,o)
  if not off or off.state!=CourseState.PUBLISHED:raise PermissionError('assignment_offering_unavailable')
  if off.cohort_id not in {e.cohort_id for e in self.campus_repo.enrollments_for_student(i,a) if e.active}:raise PermissionError('assignment_not_enrolled')
  return off
 def create(self,a,i,offering_id,*,title,instructions='',kind=AssignmentKind.INDIVIDUAL,opens_at=None,due_at,closes_at=None,max_attempts=1,max_score=20.0):
  self._teacher(a,i,offering_id)
  if not title.strip() or max_attempts<1 or max_score<=0:raise ValueError('assignment_invalid')
  if opens_at and opens_at>=due_at:raise ValueError('assignment_invalid_dates')
  if closes_at and closes_at<due_at:raise ValueError('assignment_invalid_dates')
  n=self.now();x=Assignment(uuid4().hex,i,offering_id,title.strip(),instructions.strip(),AssignmentKind(kind),opens_at,due_at,closes_at,max_attempts,float(max_score),AssignmentState.DRAFT,1,a,n,n);self.repo.save_assignment(x);self._audit(a,'assignment.created','assignment',x.id);return x
 def add_criterion(self,a,i,assignment_id,*,label,description='',max_points):
  x=self.repo.assignment(i,assignment_id)
  if not x:raise ValueError('assignment_not_found')
  self._teacher(a,i,x.offering_id)
  if x.state!=AssignmentState.DRAFT:raise ValueError('assignment_rubric_locked')
  if not label.strip() or max_points<=0:raise ValueError('assignment_invalid_criterion')
  cs=self.repo.criteria(assignment_id);c=RubricCriterion(uuid4().hex,i,assignment_id,len(cs)+1,label.strip(),description.strip(),float(max_points),self.now());self.repo.save_criterion(c);return c
 def publish(self,a,i,assignment_id,expected_version):
  x=self.repo.assignment(i,assignment_id)
  if not x:raise ValueError('assignment_not_found')
  self._teacher(a,i,x.offering_id)
  if x.row_version!=expected_version:raise ValueError('assignment_concurrent_modification')
  total=sum(c.max_points for c in self.repo.criteria(x.id))
  if total and abs(total-x.max_score)>1e-6:raise ValueError('assignment_rubric_total_mismatch')
  state=AssignmentState.SCHEDULED if x.opens_at and x.opens_at>self.now() else AssignmentState.PUBLISHED
  y=replace(x,state=state,row_version=x.row_version+1,updated_at=self.now());self.repo.save_assignment(y,x.row_version);self._audit(a,'assignment.published','assignment',x.id,{'state':state.value});return y
 def submit(self,a,i,assignment_id,*,text_content='',attachment_refs=(),group_key=None):
  x=self.repo.assignment(i,assignment_id)
  if not x:raise ValueError('assignment_not_found')
  self._student_access(a,i,x.offering_id);now=self.now()
  if x.state not in {AssignmentState.PUBLISHED,AssignmentState.SCHEDULED}:raise ValueError('assignment_not_open')
  if x.opens_at and now<x.opens_at:raise ValueError('assignment_not_open')
  if x.closes_at and now>x.closes_at:
   grants=self.repo.reopens(assignment_id) if hasattr(self.repo,'reopens') else ()
   allowed=any(g.until>=now and ((g.student_account_id==a) or (g.group_key and g.group_key==group_key) or (not g.student_account_id and not g.group_key)) for g in grants)
   if not allowed:raise ValueError('assignment_closed')
  if x.kind==AssignmentKind.GROUP:
   if not group_key:raise ValueError('assignment_group_required')
   g=self.repo.group(assignment_id,group_key)
   if not g or a not in g.member_account_ids:raise PermissionError('assignment_group_membership_required')
  prev=self.repo.submissions_for_student(assignment_id,a)
  if len(prev)>=x.max_attempts:raise ValueError('assignment_attempt_limit')
  if not text_content.strip() and not tuple(attachment_refs):raise ValueError('assignment_empty_submission')
  late=now>x.due_at;st=SubmissionState.LATE if late else SubmissionState.SUBMITTED;n=now
  s=Submission(uuid4().hex,i,assignment_id,a,group_key,len(prev)+1,text_content.strip(),tuple(attachment_refs),st,n,1,n,n);self.repo.save_submission(s);self._audit(a,'assignment.submitted','submission',s.id,{'late':late,'attempt':s.attempt_no});return s
 def propose_grade(self,a,i,submission_id,*,proposed_score,feedback='',criterion_scores=(),confidence=None,source='ai_assist'):
  s=self.repo.submission(i,submission_id)
  if not s:raise ValueError('submission_not_found')
  x=self.repo.assignment(i,s.assignment_id);self._teacher(a,i,x.offering_id)
  if proposed_score is not None and not 0<=proposed_score<=x.max_score:raise ValueError('assignment_invalid_score')
  g=GradingDecision(uuid4().hex,i,s.id,proposed_score,None,feedback.strip(),tuple(criterion_scores),confidence,source,None,self.now(),self.now());self.repo.save_grade(g);self._audit(a,'assignment.grade.proposed','grading_decision',g.id,{'source':source});return g
 def validate_grade(self,a,i,submission_id,*,final_score,feedback=None):
  s=self.repo.submission(i,submission_id)
  if not s:raise ValueError('submission_not_found')
  x=self.repo.assignment(i,s.assignment_id);self._teacher(a,i,x.offering_id)
  if not 0<=final_score<=x.max_score:raise ValueError('assignment_invalid_score')
  old=self.repo.grade_for_submission(s.id);n=self.now();g=GradingDecision(old.id if old else uuid4().hex,i,s.id,old.proposed_score if old else None,float(final_score),feedback if feedback is not None else (old.feedback if old else ''),old.criterion_scores if old else (),old.confidence if old else None,old.proposal_source if old else 'human',a,old.created_at if old else n,n);self.repo.save_grade(g);self.repo.save_submission(replace(s,state=SubmissionState.GRADED,row_version=s.row_version+1,updated_at=n),s.row_version);self._audit(a,'assignment.grade.validated','grading_decision',g.id);return g
 def similarity_flags(self,a,i,assignment_id,threshold=.75):
  x=self.repo.assignment(i,assignment_id)
  if not x:raise ValueError('assignment_not_found')
  self._teacher(a,i,x.offering_id);subs=self.repo.submissions(assignment_id);out=[]
  def tok(t):return {z for z in ''.join(ch.lower() if ch.isalnum() else ' ' for ch in t).split() if len(z)>2}
  for n,p in enumerate(subs):
   A=tok(p.text_content)
   if not A:continue
   for q in subs[n+1:]:
    B=tok(q.text_content)
    if not B:continue
    score=len(A&B)/len(A|B)
    if score>=threshold:
     f=SimilarityFlag(uuid4().hex,i,assignment_id,p.id,q.id,round(score,4),'needs_review',self.now());self.repo.save_similarity(f);out.append(f)
  return tuple(out)
 def student_assignments(self,a,i,offering_id):
  self._student_access(a,i,offering_id);return tuple(x for x in self.repo.assignments_for_offering(offering_id) if x.state in {AssignmentState.PUBLISHED,AssignmentState.SCHEDULED})

 # LOT24 v0.25.1 hardening extensions
 def transition(self,a,i,assignment_id,*,to_state,expected_version):
  x=self.repo.assignment(i,assignment_id)
  if not x:raise ValueError('assignment_not_found')
  self._teacher(a,i,x.offering_id)
  if x.row_version!=expected_version:raise ValueError('assignment_concurrent_modification')
  target=AssignmentState(to_state);allowed={
   AssignmentState.DRAFT:{AssignmentState.SCHEDULED,AssignmentState.PUBLISHED,AssignmentState.ARCHIVED},
   AssignmentState.SCHEDULED:{AssignmentState.PUBLISHED,AssignmentState.CLOSED,AssignmentState.ARCHIVED},
   AssignmentState.PUBLISHED:{AssignmentState.CLOSED,AssignmentState.GRADING},
   AssignmentState.CLOSED:{AssignmentState.GRADING,AssignmentState.PUBLISHED},
   AssignmentState.GRADING:{AssignmentState.RESULTS_PUBLISHED,AssignmentState.CLOSED},
   AssignmentState.RESULTS_PUBLISHED:{AssignmentState.GRADING,AssignmentState.ARCHIVED},
   AssignmentState.ARCHIVED:set()}
  if target not in allowed[x.state]:raise ValueError('assignment_invalid_transition')
  y=replace(x,state=target,row_version=x.row_version+1,updated_at=self.now());self.repo.save_assignment(y,x.row_version);self._audit(a,'assignment.state.changed','assignment',x.id,{'from':x.state.value,'to':target.value});return y
 def create_group(self,a,i,assignment_id,*,group_key,members):
  x=self.repo.assignment(i,assignment_id)
  if not x:raise ValueError('assignment_not_found')
  self._teacher(a,i,x.offering_id)
  if x.kind!=AssignmentKind.GROUP:raise ValueError('assignment_not_group')
  ids=tuple(dict.fromkeys(z.strip() for z in members if z.strip()))
  if not group_key.strip() or len(ids)<2:raise ValueError('assignment_invalid_group')
  for stu in ids:self._student_access(stu,i,x.offering_id)
  g=AssignmentGroup(uuid4().hex,i,x.id,group_key.strip(),ids,False,self.now());self.repo.save_group(g);self._audit(a,'assignment.group.created','assignment_group',g.id);return g
 def add_auto_item(self,a,i,assignment_id,*,kind,prompt,expected_answer,points,tolerance=None):
  x=self.repo.assignment(i,assignment_id)
  if not x:raise ValueError('assignment_not_found')
  self._teacher(a,i,x.offering_id)
  if x.state!=AssignmentState.DRAFT:raise ValueError('assignment_autograde_locked')
  k=QuestionKind(kind)
  if not prompt.strip() or not expected_answer.strip() or points<=0:raise ValueError('assignment_invalid_auto_item')
  q=AutoGradeItem(uuid4().hex,i,x.id,k,prompt.strip(),expected_answer.strip(),float(points),tolerance,self.now());self.repo.save_auto_item(q);return q
 def deterministic_grade(self,a,i,submission_id,*,answers):
  import math
  import sympy as sp
  s=self.repo.submission(i,submission_id)
  if not s:raise ValueError('submission_not_found')
  x=self.repo.assignment(i,s.assignment_id);self._teacher(a,i,x.offering_id)
  items=self.repo.auto_items(x.id);score=0.0;details=[]
  amap=dict(answers)
  for q in items:
   got=str(amap.get(q.id,'')).strip();ok=False
   if q.kind in {QuestionKind.MCQ,QuestionKind.TRUE_FALSE}:ok=got.casefold()==q.expected_answer.strip().casefold()
   elif q.kind==QuestionKind.NUMERIC:
    try:ok=math.isclose(float(got),float(q.expected_answer),abs_tol=q.tolerance or 1e-9,rel_tol=0)
    except ValueError:ok=False
   elif q.kind==QuestionKind.SYMBOLIC:
    try:ok=sp.simplify(sp.sympify(got)-sp.sympify(q.expected_answer))==0
    except Exception:ok=False
   else:continue
   if ok:score+=q.points
   details.append(f'{q.id}:{q.points if ok else 0}')
  return self.propose_grade(a,i,s.id,proposed_score=min(score,x.max_score),feedback='Correction déterministe',criterion_scores=details,confidence=1.0,source='deterministic_sympy')
 def grant_reopen(self,a,i,assignment_id,*,until,reason,student_account_id=None,group_key=None):
  x=self.repo.assignment(i,assignment_id)
  if not x:raise ValueError('assignment_not_found')
  self._teacher(a,i,x.offering_id)
  if until<=self.now() or not reason.strip() or (student_account_id and group_key):raise ValueError('assignment_invalid_reopen')
  g=ReopenGrant(uuid4().hex,i,x.id,student_account_id,group_key,until,reason.strip(),a,self.now());self.repo.save_reopen(g);self._audit(a,'assignment.reopened','assignment',x.id,{'reason':reason});return g
 def review_similarity(self,a,i,flag_id,*,decision):
  f=self.repo.similarity(flag_id)
  if not f or f.institution_id!=i:raise ValueError('similarity_not_found')
  x=self.repo.assignment(i,f.assignment_id);self._teacher(a,i,x.offering_id)
  state=ReviewState(decision);y=replace(f,review_state=state.value);self.repo.save_similarity(y);self._audit(a,'assignment.similarity.reviewed','similarity_flag',f.id,{'decision':state.value});return y
 # LOT24 v0.25.2 industrial closure
 def student_result(self,a,i,assignment_id):
  x=self.repo.assignment(i,assignment_id)
  if not x:raise ValueError('assignment_not_found')
  self._student_access(a,i,x.offering_id)
  if x.state!=AssignmentState.RESULTS_PUBLISHED:raise PermissionError('assignment_results_not_published')
  subs=self.repo.submissions_for_student(assignment_id,a)
  graded=[]
  for sub in subs:
   g=self.repo.grade_for_submission(sub.id)
   if g and g.final_score is not None:graded.append((sub,g))
  if not graded:raise ValueError('assignment_result_not_found')
  sub,g=max(graded,key=lambda z:z[0].attempt_no)
  return StudentResult(x.id,sub.id,float(g.final_score),x.max_score,g.feedback,True)
 def publish_results(self,a,i,assignment_id,*,expected_version):
  x=self.repo.assignment(i,assignment_id)
  if not x:raise ValueError('assignment_not_found')
  self._teacher(a,i,x.offering_id)
  if x.row_version!=expected_version:raise ValueError('assignment_concurrent_modification')
  if x.state!=AssignmentState.GRADING:raise ValueError('assignment_results_require_grading')
  subs=self.repo.submissions(x.id)
  if not subs:raise ValueError('assignment_results_no_submissions')
  if any((self.repo.grade_for_submission(s.id) is None or self.repo.grade_for_submission(s.id).final_score is None) for s in subs):raise ValueError('assignment_results_incomplete_grading')
  return self.transition(a,i,x.id,to_state=AssignmentState.RESULTS_PUBLISHED,expected_version=expected_version)
 def retract_results(self,a,i,assignment_id,*,expected_version,reason):
  x=self.repo.assignment(i,assignment_id)
  if not x:raise ValueError('assignment_not_found')
  self._teacher(a,i,x.offering_id)
  if x.row_version!=expected_version:raise ValueError('assignment_concurrent_modification')
  if x.state!=AssignmentState.RESULTS_PUBLISHED or not reason.strip():raise ValueError('assignment_invalid_result_retraction')
  y=self.transition(a,i,x.id,to_state=AssignmentState.GRADING,expected_version=expected_version)
  self._audit(a,'assignment.results.retracted','assignment',x.id,{'reason':reason.strip()})
  return y

