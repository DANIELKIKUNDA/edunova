from __future__ import annotations
from dataclasses import replace
from uuid import uuid4
from app.modules.academic_catalog.domain.model import *
from app.modules.campus.domain.model import UnitKind,PeriodKind,CampusRole
WRITE={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN}
class AcademicCatalogService:
 def __init__(self,repo,campus,campus_repo,source_catalog,now,audit=None):self.repo=repo;self.campus=campus;self.campus_repo=campus_repo;self.source=source_catalog;self.now=now;self.audit=audit
 def _auth(self,a,i):return self.campus.membership(a,i,WRITE)
 def _audit(self,a,action,id,meta=None):
  if self.audit:self.audit.write(actor_id=a,action=action,entity_type='academic_curriculum',entity_id=id,metadata=meta or {})
 def create(self,a,i,*,program_unit_id,effective_academic_year_id,code,title,version=1,source_catalog_id=None):
  self._auth(a,i);p=self.campus_repo.unit(i,program_unit_id);y=self.campus_repo.period(i,effective_academic_year_id);code=code.strip().upper();title=title.strip()
  if not p or p.kind!=UnitKind.PROGRAM or not p.active:raise ValueError('academic_catalog_active_program_required')
  if not y or y.kind!=PeriodKind.ACADEMIC_YEAR or not y.active:raise ValueError('academic_catalog_active_year_required')
  if version<1:raise ValueError('academic_catalog_invalid_version')
  if not code or not title:raise ValueError('academic_catalog_identity_required')
  if any(x.version==version for x in self.repo.list_curricula(i,program_unit_id)):raise ValueError('academic_catalog_version_exists')
  n=self.now();x=CurriculumVersion(uuid4().hex,i,program_unit_id,code,title,version,CurriculumState.DRAFT,effective_academic_year_id,source_catalog_id,1,a,n,None,None);self.repo.save_curriculum(x);self._audit(a,'academic.curriculum.created',x.id);return x
 def import_medicine(self,a,i,cid):
  self._auth(a,i);x=self.repo.curriculum(i,cid)
  if not x:raise ValueError('academic_catalog_not_found')
  if x.state!=CurriculumState.DRAFT:raise ValueError('academic_catalog_not_draft')
  if self.repo.courses(cid):raise ValueError('academic_catalog_already_populated')
  cat=self.source.catalog();rows=[];ordinal=0
  for s in cat['semesters']:
   for e in s['entries']:
    ordinal+=1;rows.append(CurriculumCourse(uuid4().hex,cid,s['semester'],e.get('ue') or 'UNSPECIFIED',e.get('code'),e.get('title') or '[SOURCE TITLE MISSING]',e.get('credits'),e.get('total_hours'),ordinal,s.get('cycle'),s.get('level'),e.get('ue_declared_credits'),e.get('cmi'),e.get('tp_td'),e.get('tpe'),e.get('percent')))
  self.repo.add_courses(rows);self._audit(a,'academic.curriculum.medicine_imported',cid,{'rows':len(rows),'source_catalog_id':cat['catalog_id']});return rows
 def clone_version(self,a,i,cid,*,effective_academic_year_id,version=None,code=None,title=None):
  self._auth(a,i);src=self.repo.curriculum(i,cid)
  if not src or src.state not in {CurriculumState.PUBLISHED,CurriculumState.RETIRED}:raise ValueError('academic_catalog_clone_source_required')
  existing=self.repo.list_curricula(i,src.program_unit_id);nextv=version or (max((x.version for x in existing),default=0)+1)
  dst=self.create(a,i,program_unit_id=src.program_unit_id,effective_academic_year_id=effective_academic_year_id,code=code or src.code,title=title or src.title,version=nextv,source_catalog_id=src.source_catalog_id)
  mapping={};rows=[]
  for c in self.repo.courses(cid):
   nid=uuid4().hex;mapping[c.id]=nid;rows.append(replace(c,id=nid,curriculum_id=dst.id))
  self.repo.add_courses(rows)
  for p in self.repo.prerequisites(cid):self.repo.add_prerequisite(Prerequisite(uuid4().hex,dst.id,mapping[p.course_id],mapping[p.required_course_id],p.minimum_status))
  self._audit(a,'academic.curriculum.cloned',dst.id,{'source_curriculum_id':cid,'version':nextv});return dst
 def add_prerequisite(self,a,i,cid,*,course_id,required_course_id,minimum_status='passed'):
  self._auth(a,i);x=self.repo.curriculum(i,cid);minimum_status=minimum_status.strip().lower()
  if not x or x.state!=CurriculumState.DRAFT:raise ValueError('academic_catalog_not_editable')
  if minimum_status not in {'passed','validated','completed'}:raise ValueError('academic_catalog_invalid_minimum_status')
  courses={c.id:c for c in self.repo.courses(cid)}
  if course_id not in courses or required_course_id not in courses:raise ValueError('academic_catalog_course_not_found')
  if course_id==required_course_id:raise ValueError('academic_catalog_self_prerequisite')
  graph={x:set() for x in courses}
  for p in self.repo.prerequisites(cid):graph[p.course_id].add(p.required_course_id)
  graph[course_id].add(required_course_id)
  def reaches(start,target,seen=None):
   seen=set() if seen is None else seen
   if start==target:return True
   if start in seen:return False
   seen.add(start);return any(reaches(n,target,seen) for n in graph.get(start,set()))
  if reaches(required_course_id,course_id):raise ValueError('academic_catalog_prerequisite_cycle')
  p=Prerequisite(uuid4().hex,cid,course_id,required_course_id,minimum_status);self.repo.add_prerequisite(p);self._audit(a,'academic.prerequisite.added',cid,{'course_id':course_id,'required_course_id':required_course_id});return p
 def validate(self,a,i,cid):
  self.campus.membership(a,i);x=self.repo.curriculum(i,cid)
  if not x:raise ValueError('academic_catalog_not_found')
  courses=self.repo.courses(cid);issues=[]
  if not courses:issues.append({'severity':'blocking','kind':'empty_curriculum'})
  seen=set()
  for c in courses:
   if c.semester<1:issues.append({'severity':'blocking','kind':'invalid_semester','course_id':c.id})
   if c.credits is not None and c.credits<0:issues.append({'severity':'blocking','kind':'negative_credits','course_id':c.id})
   if c.total_hours is not None and c.total_hours<0:issues.append({'severity':'blocking','kind':'negative_hours','course_id':c.id})
   if c.code:
    key=(c.semester,c.code.strip().upper())
    if key in seen:issues.append({'severity':'blocking','kind':'duplicate_course_code_in_semester','code':c.code,'semester':c.semester})
    seen.add(key)
   parts=[c.cmi,c.tp_td,c.tpe]
   if c.total_hours is not None and all(v is not None for v in parts) and sum(parts)!=c.total_hours:issues.append({'severity':'source_review','kind':'hour_components_mismatch','course_id':c.id,'computed':sum(parts),'declared':c.total_hours})
  return {'curriculum_id':cid,'course_count':len(courses),'blocking_count':sum(z['severity']=='blocking' for z in issues),'issues':issues,'publishable':not any(z['severity']=='blocking' for z in issues)}
 def publish(self,a,i,cid,expected_version):
  self._auth(a,i);x=self.repo.curriculum(i,cid)
  if not x:raise ValueError('academic_catalog_not_found')
  if x.row_version!=expected_version:raise ValueError('academic_catalog_concurrent_modification')
  if x.state!=CurriculumState.DRAFT:raise ValueError('academic_catalog_not_draft')
  report=self.validate(a,i,cid)
  if not report['publishable']:raise ValueError('academic_catalog_validation_failed')
  y=replace(x,state=CurriculumState.PUBLISHED,row_version=x.row_version+1,published_at=self.now());self.repo.save_curriculum(y,x.row_version);self._audit(a,'academic.curriculum.published',cid,{'version':x.version,'courses':report['course_count']});return y
 def retire(self,a,i,cid,expected_version):
  self._auth(a,i);x=self.repo.curriculum(i,cid)
  if not x:raise ValueError('academic_catalog_not_found')
  if x.row_version!=expected_version:raise ValueError('academic_catalog_concurrent_modification')
  if x.state!=CurriculumState.PUBLISHED:raise ValueError('academic_catalog_not_published')
  y=replace(x,state=CurriculumState.RETIRED,row_version=x.row_version+1,retired_at=self.now());self.repo.save_curriculum(y,x.row_version);self._audit(a,'academic.curriculum.retired',cid);return y
 def bind_cohort(self,a,i,cid,cohort_id):
  self._auth(a,i);x=self.repo.curriculum(i,cid);co=self.campus_repo.cohort(i,cohort_id)
  if not x or x.state!=CurriculumState.PUBLISHED:raise ValueError('academic_catalog_published_required')
  if not co or not co.active or co.program_unit_id!=x.program_unit_id:raise ValueError('academic_catalog_compatible_cohort_required')
  if self.repo.binding_for_cohort(i,cohort_id):raise ValueError('academic_catalog_cohort_already_bound')
  b=CurriculumCohortBinding(uuid4().hex,cid,cohort_id,a,self.now());self.repo.add_binding(b);self._audit(a,'academic.curriculum.cohort_bound',cid,{'cohort_id':cohort_id});return b
 def detail(self,a,i,cid):
  self.campus.membership(a,i);x=self.repo.curriculum(i,cid)
  if not x:raise ValueError('academic_catalog_not_found')
  return x,self.repo.courses(cid),self.repo.prerequisites(cid)
