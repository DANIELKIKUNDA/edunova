from __future__ import annotations
from datetime import timezone
from sqlalchemy import String,Integer,DateTime,Text,JSON,select,update
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.assessment.domain.model import *
from app.modules.assessment.domain.score_integrity import (
 verified_auto_sum, make_auto_sum_snapshot, SNAPSHOT_AUTO_SUM_VERSION
)
class QuestionRow(Base):
 __tablename__='assessment_questions';id:Mapped[str]=mapped_column(String(64),primary_key=True);bank_id:Mapped[str]=mapped_column(String(64),index=True);course_id:Mapped[str]=mapped_column(String(64),index=True);chapter_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True);kind:Mapped[str]=mapped_column(String(24));prompt:Mapped[str]=mapped_column(Text);choices:Mapped[list]=mapped_column(JSON);correct:Mapped[list]=mapped_column(JSON);explanation:Mapped[str]=mapped_column(Text);source_pages:Mapped[list]=mapped_column(JSON);provenance_sha256:Mapped[str]=mapped_column(String(64));difficulty:Mapped[int]=mapped_column(Integer);approved:Mapped[int]=mapped_column(Integer);points:Mapped[int]=mapped_column(Integer);bloom_level:Mapped[str]=mapped_column(String(24),default='understand');learning_objective:Mapped[str]=mapped_column(Text,default='');cognitive_steps:Mapped[list]=mapped_column(JSON,default=list);distractor_rationales:Mapped[list]=mapped_column(JSON,default=list);quality_score:Mapped[int]=mapped_column(Integer,default=0);clinical_vignette:Mapped[int]=mapped_column(Integer,default=0)

class QuestionOriginRow(Base):
 __tablename__='assessment_question_origins';id:Mapped[str]=mapped_column(String(64),primary_key=True);question_id:Mapped[str]=mapped_column(String(64),unique=True,index=True);source_document_id:Mapped[str]=mapped_column(String(128),index=True);source_format:Mapped[str]=mapped_column(String(24),index=True);external_id:Mapped[str|None]=mapped_column(String(255),nullable=True);original_text:Mapped[str]=mapped_column(Text);import_sha256:Mapped[str]=mapped_column(String(64));duplicate_fingerprint:Mapped[str]=mapped_column(String(64),unique=True,index=True);inferred_bloom:Mapped[str]=mapped_column(String(24),index=True);bloom_confidence:Mapped[int]=mapped_column(Integer);review_status:Mapped[str]=mapped_column(String(24),index=True);recurrent_theme:Mapped[str|None]=mapped_column(String(255),nullable=True)
def origin(r):return QuestionOrigin(r.id,r.question_id,r.source_document_id,ImportFormat(r.source_format),r.external_id,r.original_text,r.import_sha256,r.duplicate_fingerprint,BloomLevel(r.inferred_bloom),r.bloom_confidence,ReviewStatus(r.review_status),r.recurrent_theme)
class BlueprintRow(Base):
 __tablename__='assessment_blueprints';id:Mapped[str]=mapped_column(String(64),primary_key=True);title:Mapped[str]=mapped_column(String(180));course_id:Mapped[str]=mapped_column(String(64),index=True);duration_minutes:Mapped[int]=mapped_column(Integer);question_count:Mapped[int]=mapped_column(Integer);pass_percent:Mapped[int]=mapped_column(Integer);shuffle:Mapped[int]=mapped_column(Integer);approved_only:Mapped[int]=mapped_column(Integer);row_version:Mapped[int]=mapped_column(Integer);bloom_distribution:Mapped[dict|None]=mapped_column(JSON,nullable=True);min_quality_score:Mapped[int]=mapped_column(Integer,default=0)
class AttemptRow(Base):
 __tablename__='assessment_attempts';id:Mapped[str]=mapped_column(String(64),primary_key=True);account_id:Mapped[str]=mapped_column(String(64),index=True);blueprint_id:Mapped[str]=mapped_column(String(64),index=True);question_ids:Mapped[list]=mapped_column(JSON);started_at:Mapped[object]=mapped_column(DateTime(timezone=True));expires_at:Mapped[object]=mapped_column(DateTime(timezone=True));state:Mapped[str]=mapped_column(String(24),index=True);answers:Mapped[list]=mapped_column(JSON);submitted_at:Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True);row_version:Mapped[int]=mapped_column(Integer)
class ResultRow(Base):
 __tablename__='assessment_results';attempt_id:Mapped[str]=mapped_column(String(64),primary_key=True);earned:Mapped[int]=mapped_column(Integer);possible:Mapped[int]=mapped_column(Integer);percent:Mapped[int]=mapped_column(Integer);passed:Mapped[int]=mapped_column(Integer);grading_contract_version:Mapped[int]=mapped_column(Integer,default=0,server_default="0");grading_snapshot:Mapped[dict|None]=mapped_column(JSON,nullable=True);grading_snapshot_sha256:Mapped[str|None]=mapped_column(String(64),nullable=True);by_chapter:Mapped[dict]=mapped_column(JSON);by_bloom:Mapped[dict]=mapped_column(JSON,default=dict);questions:Mapped[list]=mapped_column(JSON)
def q(r):return ExamQuestion(r.id,r.bank_id,r.course_id,r.chapter_id,QuestionType(r.kind),r.prompt,tuple(r.choices),tuple(r.correct),r.explanation,tuple(r.source_pages),r.provenance_sha256,r.difficulty,bool(r.approved),r.points,BloomLevel(r.bloom_level or 'understand'),r.learning_objective or '',tuple(r.cognitive_steps or []),tuple(r.distractor_rationales or []),r.quality_score or 0,bool(r.clinical_vignette))
def b(r):return ExamBlueprint(r.id,r.title,r.course_id,r.duration_minutes,r.question_count,r.pass_percent,bool(r.shuffle),bool(r.approved_only),r.row_version,r.bloom_distribution,r.min_quality_score or 0)
def a(r):return ExamAttempt(r.id,r.account_id,r.blueprint_id,tuple(r.question_ids),r.started_at,r.expires_at,AttemptState(r.state),tuple(AttemptAnswer(x['question_id'],tuple(x['values']),x.get('marked_for_review',False)) for x in r.answers),r.submitted_at,r.row_version)
class SqlAlchemyAssessmentRepository:
 def __init__(self,sf):self.sf=sf
 def save_question(self,x):
  with self.sf() as s:s.merge(QuestionRow(**{**x.__dict__,'kind':x.kind.value,'choices':list(x.choices),'correct':list(x.correct),'source_pages':list(x.source_pages),'approved':int(x.approved),'bloom_level':x.bloom_level.value,'cognitive_steps':list(x.cognitive_steps),'distractor_rationales':list(x.distractor_rationales),'clinical_vignette':int(x.clinical_vignette)}));s.commit()
 def question(self,id):
  with self.sf() as s:r=s.get(QuestionRow,id);return q(r) if r else None
 def questions_for_course(self,c):
  with self.sf() as s:return tuple(q(r) for r in s.scalars(select(QuestionRow).where(QuestionRow.course_id==c)).all())
 def save_origin(self,x):
  with self.sf() as s:s.merge(QuestionOriginRow(**{**x.__dict__,'source_format':x.source_format.value,'inferred_bloom':x.inferred_bloom.value,'review_status':x.review_status.value}));s.commit()
 def origin_by_fingerprint(self,fp):
  with self.sf() as s:r=s.scalar(select(QuestionOriginRow).where(QuestionOriginRow.duplicate_fingerprint==fp));return origin(r) if r else None
 def origins(self,limit=100):
  with self.sf() as s:return tuple(origin(r) for r in s.scalars(select(QuestionOriginRow).limit(limit)).all())
 def delete_question(self,id):
  with self.sf() as s:r=s.get(QuestionRow,id);r is not None and s.delete(r);s.commit()
 def save_blueprint(self,x):
  with self.sf() as s:s.merge(BlueprintRow(**{**x.__dict__,'shuffle':int(x.shuffle),'approved_only':int(x.approved_only)}));s.commit()
 def blueprint(self,id):
  with self.sf() as s:r=s.get(BlueprintRow,id);return b(r) if r else None
 def save_attempt(self,x):
  with self.sf() as s:s.merge(AttemptRow(**{**x.__dict__,'state':x.state.value,'question_ids':list(x.question_ids),'answers':[{'question_id':z.question_id,'values':list(z.values),'marked_for_review':z.marked_for_review} for z in x.answers]}));s.commit()
 def attempt(self,id):
  with self.sf() as s:r=s.get(AttemptRow,id);return a(r) if r else None
 def _checked_result_row(self,s,x,attempt,blueprint):
  ids=attempt.question_ids if attempt and isinstance(attempt.question_ids,list) else []
  # FOR SHARE on PostgreSQL prevents the question bank from changing
  # between reconciliation and commit (SQLite ignores row-level locks).
  questions=s.scalars(select(QuestionRow).where(
      QuestionRow.id.in_(ids)).with_for_update(read=True)).all() if ids else []
  catalog={q.id:(q.course_id,q.points) for q in questions}
  if (not attempt or not blueprint or x.attempt_id != attempt.id or
      not verified_auto_sum(x,attempt,catalog,blueprint.course_id,blueprint.pass_percent)):
   raise ValueError('assessment_auto_sum_integrity_required')
  snapshot, digest = make_auto_sum_snapshot(x, attempt, catalog, blueprint.course_id, blueprint.pass_percent)
  return ResultRow(attempt_id=x.attempt_id,earned=x.earned,possible=x.possible,
                   percent=x.percent,passed=int(x.passed),grading_contract_version=SNAPSHOT_AUTO_SUM_VERSION,
                   grading_snapshot=snapshot,grading_snapshot_sha256=digest,
                   by_chapter=x.by_chapter,by_bloom=x.by_bloom or {},
                   questions=[z.__dict__ for z in x.questions])
 def save_graded_attempt_result(self, graded_attempt, result):
  """Atomic grade finalization; concurrent or failed submissions leave no partial grade."""
  with self.sf() as s:
   previous=s.get(AttemptRow,graded_attempt.id)
   blueprint=s.scalar(select(BlueprintRow).where(
       BlueprintRow.id==previous.blueprint_id).with_for_update(read=True)) if previous else None
   if (not previous or previous.state!='active' or
       previous.account_id!=graded_attempt.account_id or
       previous.blueprint_id!=graded_attempt.blueprint_id or
       previous.row_version!=graded_attempt.row_version-1 or
       previous.question_ids!=list(graded_attempt.question_ids) or
       graded_attempt.state!=AttemptState.GRADED or
       not graded_attempt.submitted_at or
       (graded_attempt.submitted_at.astimezone(timezone.utc) if graded_attempt.submitted_at.tzinfo else graded_attempt.submitted_at.replace(tzinfo=timezone.utc))
       <(previous.started_at.astimezone(timezone.utc) if previous.started_at.tzinfo else previous.started_at.replace(tzinfo=timezone.utc)) or
       s.get(ResultRow,graded_attempt.id) is not None):
    raise ValueError('assessment_finalization_conflict')
   row=self._checked_result_row(s,result,previous,blueprint)
   modified=s.execute(update(AttemptRow).where(AttemptRow.id==previous.id,
       AttemptRow.state=='active',AttemptRow.row_version==previous.row_version).values(
       state='graded',submitted_at=graded_attempt.submitted_at,row_version=graded_attempt.row_version))
   if modified.rowcount!=1:
    raise ValueError('assessment_finalization_conflict')
   s.add(row)
   s.commit()
 def save_result(self,x):
  """Legacy direct writer retained for compatibility, but never rewrites a grade."""
  with self.sf() as s:
   attempt=s.get(AttemptRow,x.attempt_id)
   blueprint=s.scalar(select(BlueprintRow).where(
       BlueprintRow.id==attempt.blueprint_id).with_for_update(read=True)) if attempt else None
   if not attempt or attempt.state!='graded' or s.get(ResultRow,x.attempt_id) is not None:
    raise ValueError('assessment_finalization_conflict')
   s.add(self._checked_result_row(s,x,attempt,blueprint))
   s.commit()
