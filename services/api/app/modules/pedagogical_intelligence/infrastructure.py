from sqlalchemy import select
from math import isfinite
from datetime import timezone
from app.modules.academic_delivery.infrastructure.sqlalchemy_repo import PublishedCourseResultRow, OfferingCurriculumLinkRow
from app.modules.campus_operations.infrastructure.sqlalchemy_repo import AttendanceSessionRow, AttendanceRecordRow
from app.modules.campus_operations.domain.model import AttendanceStatus

class SqlPedagogicalEvidenceRepository:
    """Read-only canonical evidence projection. Never derives student diagnoses."""
    def __init__(self, sf): self.sf=sf
    def offering_signal(self, institution_id: str, offering_id: str, allowed_accounts=None):
        """Aggregate only canonical results for the active offering cohort.

        A result for a withdrawn student, another course or a duplicate student
        registration must not manufacture evidence about this teaching group.
        Missing attendance records are *unknown*, not automatically present.
        """
        with self.sf() as s:
            link=s.scalar(select(OfferingCurriculumLinkRow).where(
                OfferingCurriculumLinkRow.institution_id==institution_id,
                OfferingCurriculumLinkRow.offering_id==offering_id))
            if not link: raise ValueError('pedintel_offering_curriculum_link_required')
            q=select(PublishedCourseResultRow).where(
                PublishedCourseResultRow.institution_id==institution_id,
                PublishedCourseResultRow.offering_id==offering_id,
                PublishedCourseResultRow.curriculum_course_id==link.curriculum_course_id)
            if allowed_accounts is not None:
                q=q.where(PublishedCourseResultRow.student_account_id.in_(allowed_accounts))
            published=s.scalars(q).all() if allowed_accounts is None or allowed_accounts else []
            # The canonical result is unique per course registration, not per
            # student: ambiguous repeat registrations are NOT two learners.
            grouped={}
            for r in published:
                grouped.setdefault(r.student_account_id,[]).append(r)
            # Two different institutional accounts may point at the same student
            # record after a merge/import error. They must NOT become two learners.
            # Both conflicting records are excluded until the SIS resolves the link.
            student_accounts = {}
            for rows in grouped.values():
                for row in rows:
                    if row.student_id:
                        student_accounts.setdefault(row.student_id, set()).add(row.student_account_id)
            ambiguous_students = {sid for sid, accounts in student_accounts.items() if len(accounts) != 1}
            results=[]
            for group in grouped.values():
                if len(group)!=1: continue  # repeated registrations fail closed
                row=group[0]
                if not row.student_id or row.student_id in ambiguous_students: continue
                try:
                    score=float(row.percent)
                except (ValueError,TypeError,OverflowError):
                    continue
                if not isfinite(score) or not 0<=score<=100: continue
                results.append(row)
            closed=s.scalars(select(AttendanceSessionRow.id).where(
                AttendanceSessionRow.institution_id==institution_id,
                AttendanceSessionRow.offering_id==offering_id,
                AttendanceSessionRow.state=='closed')).all()
            aq=select(AttendanceRecordRow).where(
                AttendanceRecordRow.institution_id==institution_id,
                AttendanceRecordRow.attendance_session_id.in_(closed))
            if allowed_accounts is not None:
                aq=aq.where(AttendanceRecordRow.student_account_id.in_(allowed_accounts))
            attendance=s.scalars(aq).all() if closed and (allowed_accounts is None or allowed_accounts) else []
            learners=(set(allowed_accounts) if allowed_accounts is not None else
                      {r.student_account_id for r in results}|{r.student_account_id for r in attendance})
            assessed=len(results)
            mean=sum(float(r.percent) for r in results)/assessed if assessed else None
            failures=sum(not bool(r.passed) for r in results)
            attended=sum(r.status in {AttendanceStatus.PRESENT.value,AttendanceStatus.LATE.value} for r in attendance)
            # No attendance-rate claim from partially recorded closed sessions.
            expected=len(closed)*len(learners)
            trusted_attendance=all(r.status in {x.value for x in AttendanceStatus}
                                   and r.review in {'clear','confirmed'} for r in attendance)
            # Even though the production table has a unique constraint, verify
            # the actual roster × closed-session matrix before claiming coverage.
            pairs={(r.attendance_session_id,r.student_account_id) for r in attendance}
            attendance_complete=(bool(expected) and len(attendance)==expected
                                 and len(pairs)==expected and trusted_attendance)
            rate=100*attended/expected if attendance_complete else None
            # Evidence digest must change when an underlying grade or review
            # changes, even if a stale upstream evidence_hash was not refreshed.
            # Identity material stays inside the digest; never expose individual IDs.
            raw_evidence=[f'result:{r.id}:{r.student_id}:{r.student_account_id}:'
                          f'{r.course_registration_id}:{r.evidence_hash}:{float(r.percent):.12g}:'
                          f'{int(r.passed)}' for r in results]
            raw_evidence += [f'attendance:{r.id}:{r.attendance_session_id}:'
                             f'{r.student_account_id}:{r.status}:{r.review}:{r.risk_score}'
                             for r in attendance]
            evidence_hash=sha256('|'.join(sorted(raw_evidence)).encode()).hexdigest() if raw_evidence else None
            return {
                'objective_id':link.curriculum_course_id,'learner_count':len(learners),'assessed_count':assessed,
                'mean_score':mean,'failure_count':failures,'attendance_rate':rate,
                'published_result_count':assessed,'closed_attendance_sessions':len(closed),
                'attendance_record_count':len(attendance), 'attendance_complete':attendance_complete,
                'evidence':({'evidence_count':len(raw_evidence),'evidence_hash':evidence_hash},),
                'curriculum_course_id':link.curriculum_course_id,
            }

from sqlalchemy import String, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from hashlib import sha256
from app.shared.infrastructure.database import Base
from app.modules.assessment.infrastructure.sqlalchemy_repo import QuestionRow, BlueprintRow, AttemptRow, ResultRow
from app.modules.assessment.domain.score_integrity import verified_auto_sum, verified_snapshot_auto_sum

class PedagogicalObjectiveRow(Base):
    __tablename__='pedagogical_learning_objectives'
    __table_args__=(UniqueConstraint('institution_id','curriculum_course_id','objective_id',name='uq_pedintel_objective_course'),)
    id:Mapped[str]=mapped_column(String(64),primary_key=True)
    institution_id:Mapped[str]=mapped_column(String(64),index=True)
    curriculum_course_id:Mapped[str]=mapped_column(String(64),index=True)
    objective_id:Mapped[str]=mapped_column(String(120),index=True)
    title:Mapped[str]=mapped_column(String(500))
    created_at:Mapped[object]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class PedagogicalQuestionObjectiveRow(Base):
    __tablename__='pedagogical_question_objectives'
    question_id:Mapped[str]=mapped_column(String(64),primary_key=True)
    institution_id:Mapped[str]=mapped_column(String(64),index=True)
    curriculum_course_id:Mapped[str]=mapped_column(String(64),index=True)
    objective_id:Mapped[str]=mapped_column(String(120),index=True)
    created_at:Mapped[object]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class PedagogicalBlueprintOfferingRow(Base):
    __tablename__='pedagogical_blueprint_offerings'
    blueprint_id:Mapped[str]=mapped_column(String(64),primary_key=True)
    institution_id:Mapped[str]=mapped_column(String(64),index=True)
    offering_id:Mapped[str]=mapped_column(String(64),index=True)
    curriculum_course_id:Mapped[str]=mapped_column(String(64),index=True)
    created_at:Mapped[object]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

def _question_result_rows(raw, allowed_questions, canonical_points=None):
    """Only canonical, unique, numerically valid questions from the graded attempt.

    Never trust result JSON alone to prove that a question was presented to the learner.
    Duplicate question IDs invalidate *all* entries for that question in the result.
    When provided, the canonical question catalog must confirm course and point value.
    """
    if not isinstance(raw, list) or not isinstance(allowed_questions, (list, tuple)):
        return ()
    if not all(isinstance(qid, str) for qid in allowed_questions):
        return ()
    allowed = set(allowed_questions)
    if len(allowed) != len(allowed_questions):
        return ()  # corrupted repeated question IDs in the canonical attempt
    counts = {}
    for row in raw:
        if isinstance(row, dict) and isinstance(row.get('question_id'), str):
            qid = row['question_id']
            counts[qid] = counts.get(qid, 0) + 1
    valid = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        qid = row.get('question_id')
        if not isinstance(qid, str) or qid not in allowed or counts.get(qid) != 1:
            continue
        possible, earned = row.get('possible'), row.get('earned')
        if (isinstance(possible, bool) or isinstance(earned, bool)
                or not isinstance(possible, (int, float)) or not isinstance(earned, (int, float))):
            continue
        possible, earned = float(possible), float(earned)
        if not (isfinite(possible) and isfinite(earned) and possible > 0 and 0 <= earned <= possible):
            continue
        if canonical_points is not None:
            point_value = canonical_points.get(qid)
            if (isinstance(point_value, bool) or not isinstance(point_value, (int, float))
                    or not isfinite(point_value) or point_value <= 0 or possible != point_value):
                continue
        # If a canonical grading verdict is present, it cannot contradict the
        # numerical score. Older results without `correct` remain readable.
        if 'correct' in row and (not isinstance(row['correct'], bool)
                                 or (row['correct'] and earned != possible)
                                 or (not row['correct'] and earned != 0)):
            continue
        valid.append((qid, earned, possible))
    return tuple(valid)

def _evidence_integrity(result, attempt, catalog, curriculum_course_id, pass_percent):
    """Return trusted score detail or explicitly unverified legacy detail.

    v1 must cover the ENTIRE graded attempt and exactly match its official
    totals, not merely the objective-mapped questions. v0 may support cautious
    historical teaching signals but never a claim of full reconciliation.
    Unknown future contracts fail closed until an implementation supports them.
    """
    version = getattr(result, 'grading_contract_version', 0)
    if type(version) is not int:
        return 'invalid'
    if version == 0:
        return 'legacy_unverified'
    if version == 2 and verified_snapshot_auto_sum(result, attempt, curriculum_course_id)[0]:
        return 'verified_snapshot_v2'
    if version == 1 and verified_auto_sum(
        result, attempt, catalog, curriculum_course_id, pass_percent
    ):
        return 'verified_auto_sum'
    return 'invalid'


def _catalog_for_attempts(session, attempts):
    ids = {qid for attempt in attempts if isinstance(attempt.question_ids, (list, tuple))
           for qid in attempt.question_ids if isinstance(qid, str)}
    if not ids:
        return {}
    rows = session.scalars(select(QuestionRow).where(QuestionRow.id.in_(ids))).all()
    return {q.id: (q.course_id, q.points) for q in rows}


def _quality_label(types, enough_group):
    if not enough_group:
        return 'suppressed'
    if types == {'verified_auto_sum'}:
        return 'verified_auto_sum'
    if types == {'verified_snapshot_v2'}:
        return 'verified_snapshot_v2'
    if types == {'verified_auto_sum', 'verified_snapshot_v2'}:
        return 'mixed_verified_contracts'
    if types == {'legacy_unverified'}:
        return 'legacy_unverified'
    if 'legacy_unverified' in types and types.issubset(
        {'verified_auto_sum', 'verified_snapshot_v2', 'legacy_unverified'}):
        return 'mixed_verified_and_legacy'
    return 'no_evidence'



def _mapping_timing(mapping, attempt):
    """Objective association provenance is distinct from score integrity.

    An objective mapped after an attempt was submitted is retrospective
    teaching metadata, not proof of the objective displayed at assessment time.
    """
    created = _utc_stamp(mapping.created_at)
    started = _utc_stamp(attempt.started_at)
    submitted = _utc_stamp(attempt.submitted_at)
    if created is None or started is None or submitted is None:
        return 'unknown'
    if created <= started:
        return 'mapped_before_attempt'
    if created <= submitted:
        return 'mapped_during_attempt'
    return 'retrospective_mapping'


def _mapping_provenance_label(values, has_evidence):
    if not has_evidence:
        return 'no_evidence'
    if 'retrospective_mapping' in values:
        return 'contains_retrospective_mapping'
    if 'unknown' in values or not values:
        return 'unknown'
    if values == {'mapped_before_attempt'}:
        return 'mapped_before_attempt'
    return 'mapped_at_or_before_submission'


def _utc_stamp(stamp):
    """Normalize PostgreSQL/SQLite datetimes without depending on SQL row order."""
    if stamp is None or not hasattr(stamp, 'tzinfo'):
        return None
    if stamp.tzinfo is None:
        return stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc)


def _valid_graded_result(result):
    """Reject impossible top-level grading totals before using answer details.

    Historical answer JSON is not necessarily a full per-attempt breakdown; its
    totals cannot be assumed to equal the official grade. The official totals,
    however, must be internally coherent and finite to support an analysis.
    """
    earned, possible, percent, passed = (result.earned, result.possible,
                                          result.percent, result.passed)
    if any(isinstance(v, bool) or not isinstance(v, (int, float))
           or not isfinite(v) for v in (earned, possible, percent)):
        return False
    if possible <= 0 or earned < 0 or earned > possible or not 0 <= percent <= 100:
        return False
    if passed not in (0, 1) or isinstance(passed, bool):
        return False
    # The score may be an integer rounded from fractional points. Allow a
    # point of rounding tolerance, not a contradictory percentage.
    return abs(percent - 100 * earned / possible) <= 1.0


def _valid_graded_attempt(attempt):
    started = _utc_stamp(attempt.started_at)
    submitted = _utc_stamp(attempt.submitted_at)
    # A grade without a submission, or submitted before the attempt began,
    # cannot become canonical pedagogical evidence.
    return bool(started is not None and submitted is not None and submitted >= started)


def _latest_graded_attempts(attempts):
    """Select one *latest-started* graded attempt per account and blueprint.

    A new retake supersedes the old one even when its submission timestamp is
    missing or corrupted. Validate the winning attempt *after* selection so a
    compromised retake cannot silently resurrect an obsolete grade.
    """
    latest = {}
    for attempt in attempts:
        started = _utc_stamp(attempt.started_at)
        if started is None:
            continue
        submitted = _utc_stamp(attempt.submitted_at)
        key = (attempt.account_id, attempt.blueprint_id)
        order = (started, submitted or started, attempt.id)
        if key not in latest or order > latest[key][0]:
            latest[key] = (order, attempt)
    return tuple(item[1] for item in latest.values())


def _canonical_question_points(session, institution_id, curriculum_course_id, question_mappings):
    """Validate the question's current canonical course and point value.

    Binding metadata alone cannot authorize an outdated or cross-course question.
    """
    ids = set(question_mappings)
    if not ids:
        return {}
    rows = session.scalars(select(QuestionRow).where(
        QuestionRow.id.in_(ids), QuestionRow.course_id == curriculum_course_id)).all()
    return {row.id: row.points for row in rows if isinstance(row.points, int) and row.points > 0}


class SqlObjectiveEvidenceRepository(SqlPedagogicalEvidenceRepository):
    def upsert_objective(self,institution_id,curriculum_course_id,objective_id,title):
        from uuid import uuid4
        with self.sf() as s:
            row=s.scalar(select(PedagogicalObjectiveRow).where(PedagogicalObjectiveRow.institution_id==institution_id,PedagogicalObjectiveRow.curriculum_course_id==curriculum_course_id,PedagogicalObjectiveRow.objective_id==objective_id))
            if row: row.title=title
            else:s.add(PedagogicalObjectiveRow(id=uuid4().hex,institution_id=institution_id,curriculum_course_id=curriculum_course_id,objective_id=objective_id,title=title))
            s.commit()
    def map_question(self,institution_id,curriculum_course_id,objective_id,question_id):
        with self.sf() as s:
            obj=s.scalar(select(PedagogicalObjectiveRow).where(PedagogicalObjectiveRow.institution_id==institution_id,PedagogicalObjectiveRow.curriculum_course_id==curriculum_course_id,PedagogicalObjectiveRow.objective_id==objective_id))
            q=s.get(QuestionRow,question_id)
            if not obj: raise ValueError('pedintel_objective_not_found')
            if not q or q.course_id!=curriculum_course_id: raise ValueError('pedintel_question_course_mismatch')
            old=s.get(PedagogicalQuestionObjectiveRow,question_id)
            if old and (old.institution_id!=institution_id or old.curriculum_course_id!=curriculum_course_id or old.objective_id!=objective_id): raise ValueError('pedintel_question_mapping_conflict')
            if old: return  # idempotent; an existing mapping must never be updated
            self._insert_immutable(s,PedagogicalQuestionObjectiveRow,'question_id',question_id,
                                   dict(question_id=question_id,institution_id=institution_id,curriculum_course_id=curriculum_course_id,objective_id=objective_id),
                                   'pedintel_question_mapping_conflict')
    def bind_blueprint(self,institution_id,offering_id,curriculum_course_id,blueprint_id):
        with self.sf() as s:
            b=s.get(BlueprintRow,blueprint_id)
            if not b or b.course_id!=curriculum_course_id: raise ValueError('pedintel_blueprint_course_mismatch')
            old=s.get(PedagogicalBlueprintOfferingRow,blueprint_id)
            if old and (old.institution_id!=institution_id or old.offering_id!=offering_id or old.curriculum_course_id!=curriculum_course_id): raise ValueError('pedintel_blueprint_binding_conflict')
            if old: return
            self._insert_immutable(s,PedagogicalBlueprintOfferingRow,'blueprint_id',blueprint_id,
                                   dict(blueprint_id=blueprint_id,institution_id=institution_id,offering_id=offering_id,curriculum_course_id=curriculum_course_id),
                                   'pedintel_blueprint_binding_conflict')
    @staticmethod
    def _insert_immutable(s, model, key_column, key, values, conflict_error):
        """Atomic insert-if-absent + verification; a simultaneous writer never gets overwritten."""
        dialect=s.get_bind().dialect.name
        if dialect=='postgresql':
            from sqlalchemy.dialects.postgresql import insert
            stmt=insert(model).values(**values).on_conflict_do_nothing(index_elements=[key_column])
            s.execute(stmt)
        elif dialect=='sqlite':  # local regression only; PostgreSQL is the production target
            from sqlalchemy.dialects.sqlite import insert
            stmt=insert(model).values(**values).on_conflict_do_nothing(index_elements=[key_column])
            s.execute(stmt)
        else:
            raise RuntimeError('pedintel_unsupported_atomic_mapping_dialect')
        persisted=s.get(model,key)
        if not persisted or any(getattr(persisted, field)!=value for field,value in values.items()):
            raise ValueError(conflict_error)
        s.commit()
    def objective_signals(self,institution_id,offering_id,allowed_accounts=None):
        with self.sf() as s:
            link=s.scalar(select(OfferingCurriculumLinkRow).where(OfferingCurriculumLinkRow.institution_id==institution_id,OfferingCurriculumLinkRow.offering_id==offering_id))
            if not link: raise ValueError('pedintel_offering_curriculum_link_required')
            objs=s.scalars(select(PedagogicalObjectiveRow).where(PedagogicalObjectiveRow.institution_id==institution_id,PedagogicalObjectiveRow.curriculum_course_id==link.curriculum_course_id)).all()
            binds=s.scalars(select(PedagogicalBlueprintOfferingRow).where(PedagogicalBlueprintOfferingRow.institution_id==institution_id,PedagogicalBlueprintOfferingRow.offering_id==offering_id,PedagogicalBlueprintOfferingRow.curriculum_course_id==link.curriculum_course_id)).all()
            blueprint_ids={x.blueprint_id for x in binds}
            real_blueprints=s.scalars(select(BlueprintRow).where(
                BlueprintRow.id.in_(blueprint_ids), BlueprintRow.course_id==link.curriculum_course_id)).all() if blueprint_ids else ()
            blueprint_ids={b.id for b in real_blueprints}
            blueprint_pass={b.id:b.pass_percent for b in real_blueprints}
            query=select(AttemptRow).where(AttemptRow.blueprint_id.in_(blueprint_ids),AttemptRow.state=='graded')
            if allowed_accounts is not None:
                query=query.where(AttemptRow.account_id.in_(allowed_accounts))
            attempts=_latest_graded_attempts(s.scalars(query).all()) if blueprint_ids and (allowed_accounts is None or allowed_accounts) else ()
            attempt_ids={a.id for a in attempts}; by_attempt={a.id:a for a in attempts}
            results=s.scalars(select(ResultRow).where(ResultRow.attempt_id.in_(attempt_ids))).all() if attempt_ids else []
            catalog=_catalog_for_attempts(s,attempts)
            maps=s.scalars(select(PedagogicalQuestionObjectiveRow).where(PedagogicalQuestionObjectiveRow.institution_id==institution_id,PedagogicalQuestionObjectiveRow.curriculum_course_id==link.curriculum_course_id)).all()
            qmap={m.question_id:m.objective_id for m in maps};
            mapping_by_question={m.question_id:m for m in maps};
            points=_canonical_question_points(s,institution_id,link.curriculum_course_id,qmap)
            per={o.objective_id:{} for o in objs}; evidence={o.objective_id:[] for o in objs}
            quality={o.objective_id:set() for o in objs}
            mapping_quality={o.objective_id:set() for o in objs}
            for r in results:
                attempt=by_attempt.get(r.attempt_id)
                if not attempt or not _valid_graded_attempt(attempt) or not _valid_graded_result(r): continue
                # A "graded" row without a submission timestamp is not a
                # completed assessment. Do not resurrect an older retake.
                integrity=_evidence_integrity(r,attempt,catalog,link.curriculum_course_id,
                                              blueprint_pass[attempt.blueprint_id])
                if integrity=='invalid': continue
                # v2 uses the recorded grading-time point values; v0/v1
                # deliberately keep their stricter mutable-catalog constraints.
                row_points=(verified_snapshot_auto_sum(r,attempt,link.curriculum_course_id)[1]
                            if integrity=='verified_snapshot_v2' else points)
                for qid,earned,possible in _question_result_rows(r.questions,attempt.question_ids,row_points):
                    if qid not in row_points: continue
                    oid=qmap.get(qid)
                    if oid not in per: continue
                    bucket=per[oid].setdefault(attempt.account_id,[0.0,0.0]);bucket[0]+=earned;bucket[1]+=possible
                    quality[oid].add(integrity)
                    mapping_quality[oid].add(_mapping_timing(mapping_by_question[qid],attempt))
                    evidence[oid].append(f'assessment:{r.attempt_id}:{qid}:{earned:g}/{possible:g}')
            out=[]
            for o in objs:
                learner_scores=[100*earned/possible for earned,possible in per[o.objective_id].values() if possible>0]
                assessed=len(learner_scores); mean=sum(learner_scores)/assessed if assessed else None; failures=sum(v<60 for v in learner_scores)
                raw=sorted(evidence[o.objective_id]); digest=sha256('|'.join(raw).encode()).hexdigest() if raw else None
                # Minimum aggregate cell size: one or two learners must not reveal
                # their grades, failures or even an attempt-derived evidence hash.
                enough_group = assessed >= 3
                out.append({'objective_id':o.objective_id,'objective_title':o.title,
                            'learner_count':len(allowed_accounts) if allowed_accounts is not None else assessed,
                            'assessed_count':assessed,'mean_score':mean if enough_group else None,
                            'failure_count':failures if enough_group else 0,'attendance_rate':None,
                            'question_evidence_count':len(raw) if enough_group else None,
                            'evidence_hash':digest if enough_group else None,
                            'aggregate_suppressed':not enough_group,
                            'evidence_integrity':_quality_label(quality[o.objective_id],enough_group),
                            'mapping_provenance':(_mapping_provenance_label(mapping_quality[o.objective_id],bool(raw)) if enough_group else 'suppressed')})
            return tuple(out)
    def objective_trends(self,institution_id,offering_id,allowed_accounts=None):
        """Assessment-by-assessment objective evidence; aggregate only, no learner profiling."""
        with self.sf() as s:
            link=s.scalar(select(OfferingCurriculumLinkRow).where(OfferingCurriculumLinkRow.institution_id==institution_id,OfferingCurriculumLinkRow.offering_id==offering_id))
            if not link: raise ValueError('pedintel_offering_curriculum_link_required')
            objs=s.scalars(select(PedagogicalObjectiveRow).where(PedagogicalObjectiveRow.institution_id==institution_id,PedagogicalObjectiveRow.curriculum_course_id==link.curriculum_course_id)).all()
            binds=s.scalars(select(PedagogicalBlueprintOfferingRow).where(PedagogicalBlueprintOfferingRow.institution_id==institution_id,PedagogicalBlueprintOfferingRow.offering_id==offering_id,PedagogicalBlueprintOfferingRow.curriculum_course_id==link.curriculum_course_id)).all()
            blueprint_ids={x.blueprint_id for x in binds}
            real_blueprints=s.scalars(select(BlueprintRow).where(
                BlueprintRow.id.in_(blueprint_ids), BlueprintRow.course_id==link.curriculum_course_id)).all() if blueprint_ids else ()
            blueprint_ids={b.id for b in real_blueprints}
            blueprint_pass={b.id:b.pass_percent for b in real_blueprints}
            query=select(AttemptRow).where(AttemptRow.blueprint_id.in_(blueprint_ids),AttemptRow.state=='graded')
            if allowed_accounts is not None:
                query=query.where(AttemptRow.account_id.in_(allowed_accounts))
            attempts=_latest_graded_attempts(s.scalars(query).all()) if blueprint_ids and (allowed_accounts is None or allowed_accounts) else ()
            amap={a.id:a for a in attempts}; attempt_ids=set(amap)
            results=s.scalars(select(ResultRow).where(ResultRow.attempt_id.in_(attempt_ids))).all() if attempt_ids else []
            catalog=_catalog_for_attempts(s,attempts)
            maps=s.scalars(select(PedagogicalQuestionObjectiveRow).where(PedagogicalQuestionObjectiveRow.institution_id==institution_id,PedagogicalQuestionObjectiveRow.curriculum_course_id==link.curriculum_course_id)).all()
            qmap={m.question_id:m.objective_id for m in maps};
            mapping_by_question={m.question_id:m for m in maps};
            points=_canonical_question_points(s,institution_id,link.curriculum_course_id,qmap)
            titles={o.objective_id:o.title for o in objs}
            # period = blueprint: objective scores are aggregated per learner first, then across learners.
            periods={}
            period_quality={}
            period_mapping_quality={}
            missed={}
            missed_quality={}
            missed_mapping_quality={}
            for r in results:
                a=amap.get(r.attempt_id)
                if not a or not _valid_graded_attempt(a) or not _valid_graded_result(r): continue
                integrity=_evidence_integrity(r,a,catalog,link.curriculum_course_id,
                                              blueprint_pass[a.blueprint_id])
                if integrity=='invalid': continue
                key=a.blueprint_id; per=periods.setdefault(key,{})
                row_points=(verified_snapshot_auto_sum(r,a,link.curriculum_course_id)[1]
                            if integrity=='verified_snapshot_v2' else points)
                for qid,earned,possible in _question_result_rows(r.questions,a.question_ids,row_points):
                    if qid not in row_points: continue
                    oid=qmap.get(qid)
                    if oid not in titles: continue
                    learner=per.setdefault(oid,{}).setdefault(a.account_id,[0.0,0.0]); learner[0]+=earned;learner[1]+=possible
                    period_quality.setdefault((key,oid),set()).add(integrity)
                    timing=_mapping_timing(mapping_by_question[qid],a)
                    period_mapping_quality.setdefault((key,oid),set()).add(timing)
                    if earned < possible:
                        missed.setdefault((oid,qid),set()).add(a.account_id)
                        missed_quality.setdefault((oid,qid),set()).add(integrity)
                        missed_mapping_quality.setdefault((oid,qid),set()).add(timing)
            timeline=[]
            for blueprint_id,odata in periods.items():
                for oid,learners in odata.items():
                    scores=[100*e/p for e,p in learners.values() if p>0]
                    if len(scores)<3: continue  # prevent small-cell grade disclosure
                    timeline.append({'blueprint_id':blueprint_id,'objective_id':oid,'objective_title':titles[oid],'assessed_count':len(scores),'mean_score':sum(scores)/len(scores),'failure_count':sum(v<60 for v in scores),
                                     'evidence_integrity':_quality_label(period_quality.get((blueprint_id,oid),set()),True),
                                     'mapping_provenance':_mapping_provenance_label(period_mapping_quality.get((blueprint_id,oid),set()),True)})
            # A recurrent error is reported only as a group-level missed-question signal with >=3 distinct learners.
            misconceptions=[]
            for (oid,qid),learners in missed.items():
                if len(learners)>=3:
                    misconceptions.append({'objective_id':oid,'objective_title':titles[oid],'question_id':qid,'affected_learner_count':len(learners),'interpretation':'recurrent_incorrect_response','diagnosis':False,
                                          'evidence_integrity':_quality_label(missed_quality.get((oid,qid),set()),True),
                                          'mapping_provenance':_mapping_provenance_label(missed_mapping_quality.get((oid,qid),set()),True)})
            return {'timeline':tuple(sorted(timeline,key=lambda x:(x['objective_id'],x['blueprint_id']))),'recurrent_errors':tuple(sorted(misconceptions,key=lambda x:(x['objective_id'],-x['affected_learner_count'],x['question_id'])))}

    def gradebook_assessment_reconciliation(self, institution_id, offering_id, allowed_accounts=None):
        """Read-only corroboration of *candidate* assessment references in a published gradebook.

        Gradebook source_ref is staff-editable. Even an exact score match does NOT
        authenticate the reference or certify the gradebook or jury publication.
        Never return individual marks or identities; suppress groups of <3.
        """
        from app.modules.gradebook.infrastructure.sqlalchemy_repo import GradebookRow, ComponentRow, MarkRow
        from app.modules.gradebook.domain.model import GradebookState, ComponentKind
        base = {'scope': 'published_gradebook_assessment_candidates',
                'offering_id': offering_id, 'authoritative_source_link': False,
                'official_grade_modified': False,
                'limitations': (
                    'Gradebook mark source_ref is staff-editable and not an authenticated grade publication link.',
                    'A matching candidate score does not certify the gradebook, transcript or jury decision.',
                    'Only existing auto-graded v2 snapshots are corroborated; manual/legacy evidence needs separate review.',
                )}
        with self.sf() as s:
            link=s.scalar(select(OfferingCurriculumLinkRow).where(
                OfferingCurriculumLinkRow.institution_id==institution_id,
                OfferingCurriculumLinkRow.offering_id==offering_id))
            if not link: raise ValueError('pedintel_offering_curriculum_link_required')
            g=s.scalar(select(GradebookRow).where(
                GradebookRow.institution_id==institution_id,
                GradebookRow.offering_id==offering_id))
            if not g or g.state != GradebookState.PUBLISHED.value:
                return {**base,'status':'no_published_gradebook','candidate_count':None,
                        'score_discrepancies':None}
            comps=s.scalars(select(ComponentRow).where(
                ComponentRow.institution_id==institution_id,ComponentRow.gradebook_id==g.id,
                ComponentRow.kind.in_([ComponentKind.TEST.value,ComponentKind.EXAM.value]))).all()
            component_map={c.id:c for c in comps}
            if not component_map or allowed_accounts is not None and not allowed_accounts:
                return {**base,'status':'no_candidate_links','candidate_count':None,
                        'score_discrepancies':None}
            stmt=select(MarkRow).where(MarkRow.institution_id==institution_id,
                MarkRow.gradebook_id==g.id,MarkRow.component_id.in_(component_map))
            if allowed_accounts is not None:
                stmt=stmt.where(MarkRow.student_account_id.in_(allowed_accounts))
            marks=s.scalars(stmt).all()
            candidate=[m for m in marks if isinstance(m.source_ref,str) and m.source_ref.startswith('assessment:')]
            if not candidate:
                return {**base,'status':'no_candidate_links','candidate_count':None,
                        'score_discrepancies':None}
            # Suppress before querying referenced attempts. Both small cohort and
            # reused one-student references must not become a learner-level oracle.
            if (allowed_accounts is None or len(allowed_accounts)<3 or
                len({m.student_account_id for m in candidate})<3):
                return {**base,'status':'suppressed','candidate_count':None,
                        'score_discrepancies':None}
            ref_ids={m.source_ref[len('assessment:'):] for m in candidate
                     if len(m.source_ref)>len('assessment:')}
            attempts={a.id:a for a in s.scalars(select(AttemptRow).where(
                AttemptRow.id.in_(ref_ids))).all()} if ref_ids else {}
            results={r.attempt_id:r for r in s.scalars(select(ResultRow).where(
                ResultRow.attempt_id.in_(ref_ids))).all()} if ref_ids else {}
            binds={b.blueprint_id for b in s.scalars(select(PedagogicalBlueprintOfferingRow).where(
                PedagogicalBlueprintOfferingRow.institution_id==institution_id,
                PedagogicalBlueprintOfferingRow.offering_id==offering_id,
                PedagogicalBlueprintOfferingRow.curriculum_course_id==link.curriculum_course_id)).all()}
            blueprints={b.id:b for b in s.scalars(select(BlueprintRow).where(
                BlueprintRow.id.in_(binds),BlueprintRow.course_id==link.curriculum_course_id)).all()} if binds else {}
            seen=set(); discrepancies=0
            for mark in candidate:
                aid=mark.source_ref[len('assessment:'):]
                a=attempts.get(aid); r=results.get(aid); c=component_map[mark.component_id]
                # Prevent copying the same attempt into multiple exam components.
                unique=(mark.student_account_id,aid)
                duplicate=unique in seen
                seen.add(unique)
                trustworthy=(not duplicate and a is not None and r is not None
                    and mark.state=='validated' and mark.attendance=='present'
                    and a.state=='graded' and a.account_id==mark.student_account_id
                    and a.blueprint_id in blueprints and _valid_graded_attempt(a)
                    and _valid_graded_result(r)
                    and type(getattr(r,'grading_contract_version',None)) is int
                    and r.grading_contract_version==2
                    and verified_snapshot_auto_sum(r,a,link.curriculum_course_id)[0])
                score=getattr(mark,'score',None)
                max_score=c.max_score
                if (not trustworthy or isinstance(score,bool) or isinstance(max_score,bool)
                    or not isinstance(score,(float,int)) or not isinstance(max_score,(float,int))
                    or not isfinite(score) or not isfinite(max_score) or max_score<=0
                    or score<0 or score>max_score
                    or abs(100*score/max_score - 100*r.earned/r.possible)>0.51):
                    discrepancies+=1
            return {**base,
                'status':'candidate_scores_consistent' if not discrepancies else 'manual_review_required',
                'candidate_count':len(candidate),'score_discrepancies':discrepancies}
