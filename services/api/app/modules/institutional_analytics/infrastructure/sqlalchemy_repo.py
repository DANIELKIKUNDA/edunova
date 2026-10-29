from __future__ import annotations
from collections import defaultdict
import json
import hmac
from hashlib import sha256
from math import isfinite
from datetime import UTC, datetime
from uuid import uuid4
from sqlalchemy import select, func, String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.exc import IntegrityError
from app.shared.infrastructure.database import Base
from app.modules.campus.infrastructure.sqlalchemy_repo import EnrollmentRow, CohortRow, UnitRow
from app.modules.teaching.infrastructure.sqlalchemy_repo import OfferingRow, SessionRow, TopicRow, SyllabusRow
from app.modules.assignments.infrastructure.sqlalchemy_repo import AssignmentRow, SubmissionRow
from app.modules.gradebook.infrastructure.sqlalchemy_repo import GradebookRow, ComponentRow, MarkRow
from app.modules.campus_operations.infrastructure.sqlalchemy_repo import AttendanceSessionRow, AttendanceRecordRow
from app.modules.assessment.infrastructure.sqlalchemy_repo import AttemptRow, ResultRow, BlueprintRow, QuestionRow
from app.modules.knowledge_graph.infrastructure.sqlalchemy_repo import NodeRow, RelationRow


class InstitutionalAnalyticsSnapshotRow(Base):
    __tablename__='institutional_analytics_snapshots'
    id:Mapped[str]=mapped_column(String(64),primary_key=True)
    institution_id:Mapped[str]=mapped_column(String(64),index=True)
    scope_type:Mapped[str]=mapped_column(String(24),index=True)
    scope_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True)
    academic_period_id:Mapped[str|None]=mapped_column(String(64),nullable=True,index=True)
    metric_contract_version:Mapped[int]=mapped_column(Integer,default=1)
    payload_json:Mapped[str]=mapped_column(Text)
    source_watermark:Mapped[str]=mapped_column(String(128))
    generated_at:Mapped[object]=mapped_column(DateTime(timezone=True),index=True)

class InstitutionalAnalyticsLiveReleaseRow(Base):
    """One immutable policy commitment per institution and *exact* live scope.

    No student IDs, raw scores, rates, or population member hashes are stored.
    A server-keyed HMAC commits to both population and released aggregates.
    A unique composite PK arbitrates simultaneous first releases.
    """
    __tablename__='institutional_analytics_live_releases'
    institution_id:Mapped[str]=mapped_column(String(64),primary_key=True)
    scope_key:Mapped[str]=mapped_column(String(64),primary_key=True)
    scope_json:Mapped[str]=mapped_column(Text)
    nonce:Mapped[str]=mapped_column(String(48))
    disclosure_hmac:Mapped[str]=mapped_column(String(64))
    contract_version:Mapped[int]=mapped_column(Integer,default=1)
    first_released_at:Mapped[object]=mapped_column(DateTime(timezone=True))

class SqlAlchemyInstitutionalAnalyticsRepository:
    '''Read-only projection over institutional bounded contexts. It never reads personal-library, tutor or private-study tables.'''
    def __init__(self,sf): self.sf=sf
    def descendant_program_ids(self,i,unit_id):
        with self.sf() as s:
            rows=s.scalars(select(UnitRow).where(UnitRow.institution_id==i,UnitRow.active==True)).all()
        children=defaultdict(list)
        for r in rows: children[r.parent_id].append(r)
        out=[]; stack=[unit_id]; seen=set()
        while stack:
            cur=stack.pop()
            if cur in seen: continue
            seen.add(cur)
            for r in children.get(cur,[]):
                if r.kind=='program': out.append(r.id)
                stack.append(r.id)
        root=next((r for r in rows if r.id==unit_id),None)
        if root and root.kind=='program': out.append(root.id)
        return tuple(dict.fromkeys(out))
    def cohort_ids_for_unit(self,i,unit_id,period_id=None):
        programs=self.descendant_program_ids(i,unit_id)
        if not programs:return ()
        with self.sf() as s:
            q=select(CohortRow.id).where(CohortRow.institution_id==i,CohortRow.program_unit_id.in_(programs),CohortRow.active==True)
            if period_id:q=q.where(CohortRow.academic_period_id==period_id)
            return tuple(s.scalars(q).all())
    def snapshot_for_unit(self,i,unit_id,period_id=None,governed=False):
        cohorts=self.cohort_ids_for_unit(i,unit_id,period_id)
        if not cohorts:
            d=self._empty(i,period_id,None,None);d['scope']['academic_unit_id']=unit_id;return d
        ids=[]
        for c in cohorts: ids.extend(self.offering_ids(i,period_id,c))
        
        if not ids:
            d=self._empty(i,period_id,None,None);d['scope']['academic_unit_id']=unit_id;return d
        return self.snapshot(i,period_id,offering_ids=tuple(dict.fromkeys(ids)),academic_unit_id=unit_id,governed=governed)
    # Internal v4 population proof is NOT part of the published archive payload.
    # A random nonce + server-keyed HMAC prevents unkeyed ID-list dictionary
    # matching and does not disclose student identities through the API.
    def population_membership_proof(self,i,*,period_id=None,academic_unit_id=None,
                                    cohort_id=None,offering_id=None,nonce,secret):
        if not isinstance(secret,str) or len(secret)<32:
            raise RuntimeError('institutional_analytics_archive_secret_not_configured')
        if academic_unit_id:
            cohorts=self.cohort_ids_for_unit(i,academic_unit_id,period_id)
        elif offering_id:
            with self.sf() as s:
                query=select(OfferingRow.cohort_id).where(
                    OfferingRow.institution_id==i,OfferingRow.id==offering_id)
                if period_id:query=query.where(OfferingRow.academic_period_id==period_id)
                if cohort_id:query=query.where(OfferingRow.cohort_id==cohort_id)
                cohorts=tuple(s.scalars(query).all())
        else:
            with self.sf() as s:
                query=select(OfferingRow.cohort_id).where(OfferingRow.institution_id==i)
                if period_id:query=query.where(OfferingRow.academic_period_id==period_id)
                if cohort_id:query=query.where(OfferingRow.cohort_id==cohort_id)
                cohorts=tuple(s.scalars(query.distinct()).all())
        accounts=[]
        if cohorts:
            valid=select(CohortRow.id).where(CohortRow.institution_id==i,
                CohortRow.active==True,CohortRow.id.in_(cohorts))
            if period_id:valid=valid.where(CohortRow.academic_period_id==period_id)
            with self.sf() as s:
                accounts=sorted(s.scalars(select(EnrollmentRow.student_account_id).where(
                    EnrollmentRow.institution_id==i,EnrollmentRow.active==True,
                    EnrollmentRow.cohort_id.in_(valid)).distinct()).all())
        body=json.dumps({'version':4,'institution':i,'period':period_id,
            'unit':academic_unit_id,'cohort':cohort_id,'offering':offering_id,
            'nonce':nonce,'accounts':accounts},sort_keys=True,separators=(',',':'))
        return hmac.new(secret.encode(),body.encode(),sha256).hexdigest()

    def save_immutable_snapshot(self,i,payload,scope_type,scope_id=None,period_id=None,generated_at=None,metric_contract_version=1,private_proof=None):
        generated_at=generated_at or datetime.now(UTC)
        if metric_contract_version>=4 and not private_proof:
            raise ValueError('institutional_analytics_v4_proof_required')
        stored=dict(payload)
        if private_proof is not None:
            stored['_internal_archive_proof']=private_proof
        canonical=json.dumps(stored,sort_keys=True,separators=(',',':'),ensure_ascii=False)
        digest=sha256(canonical.encode()).hexdigest()
        row=InstitutionalAnalyticsSnapshotRow(id=uuid4().hex,institution_id=i,scope_type=scope_type,scope_id=scope_id,academic_period_id=period_id,metric_contract_version=metric_contract_version,payload_json=canonical,source_watermark=digest,generated_at=generated_at)
        with self.sf() as s:s.add(row);s.commit();s.refresh(row)
        return {'id':row.id,'institution_id':i,'scope_type':scope_type,'scope_id':scope_id,'academic_period_id':period_id,'metric_contract_version':metric_contract_version,'payload':payload,'content_sha256':digest,'generated_at':row.generated_at}
    def list_snapshots(self,i,scope_type,scope_id=None,period_id=None,limit=50):
        with self.sf() as s:
            q=select(InstitutionalAnalyticsSnapshotRow).where(InstitutionalAnalyticsSnapshotRow.institution_id==i,InstitutionalAnalyticsSnapshotRow.scope_type==scope_type)
            if scope_id is not None:q=q.where(InstitutionalAnalyticsSnapshotRow.scope_id==scope_id)
            if period_id is not None:q=q.where(InstitutionalAnalyticsSnapshotRow.academic_period_id==period_id)
            rows=s.scalars(q.order_by(InstitutionalAnalyticsSnapshotRow.generated_at.desc()).limit(min(max(limit,1),200))).all()
            return tuple({'id':r.id,'scope_type':r.scope_type,'scope_id':r.scope_id,'academic_period_id':r.academic_period_id,'metric_contract_version':r.metric_contract_version,'payload':json.loads(r.payload_json),'stored_integrity_ok':sha256(r.payload_json.encode()).hexdigest()==r.source_watermark,'content_sha256':r.source_watermark,'generated_at':r.generated_at} for r in rows)
    def first_snapshot_id(self,i,scope_type,scope_id=None):
        """Earliest release for this institution and scope, across *all* periods.

        Looking only at the newest row or filtering by period creates a temporal
        differencing loophole. Never use history's client-controlled limit here.
        """
        with self.sf() as s:
            q=select(InstitutionalAnalyticsSnapshotRow.id).where(
                InstitutionalAnalyticsSnapshotRow.institution_id==i,
                InstitutionalAnalyticsSnapshotRow.scope_type==scope_type)
            if scope_id is None:
                q=q.where(InstitutionalAnalyticsSnapshotRow.scope_id.is_(None))
            else:
                q=q.where(InstitutionalAnalyticsSnapshotRow.scope_id==scope_id)
            return s.scalar(q.order_by(InstitutionalAnalyticsSnapshotRow.generated_at.asc(),
                                       InstitutionalAnalyticsSnapshotRow.id.asc()).limit(1))

    def check_or_lock_live_release(self,i,scope,projection,secret):
        """Permanent per-scope release: never disclose a second changed projection.

        A content/personal-membership keyed commitment avoids storing identities.
        Optimistic insert with database PK resolves first-release races. This
        does NOT replace a production PostgreSQL transaction isolation test.
        """
        import secrets as crypto_secrets
        scope_json=json.dumps(scope,sort_keys=True,separators=(',',':'))
        scope_key=sha256(scope_json.encode()).hexdigest()
        payload=json.dumps(projection,sort_keys=True,separators=(',',':'),ensure_ascii=False)
        if not isinstance(secret,str) or len(secret)<32:
            return False
        for _ in range(2):
            with self.sf() as s:
                row=s.get(InstitutionalAnalyticsLiveReleaseRow,(i,scope_key))
                if row is not None:
                    if row.scope_json!=scope_json or row.contract_version!=1:
                        return False
                    nonce=row.nonce
                else:
                    nonce=crypto_secrets.token_hex(24)
                # Even if every rate happens to be unchanged, replacing one
                # learner may enable inference when other scopes are consulted.
                population_proof=self.population_membership_proof(i,
                    period_id=scope.get('academic_period_id'),
                    academic_unit_id=scope.get('academic_unit_id'),
                    cohort_id=scope.get('cohort_id'),
                    offering_id=scope.get('offering_id'),
                    nonce=nonce,secret=secret)
                msg=json.dumps({'contract_version':1,'institution':i,
                    'scope':scope,'nonce':nonce,'population_hmac':population_proof,
                    'projection':payload},sort_keys=True,separators=(',',':'))
                fingerprint=hmac.new(secret.encode(),msg.encode(),sha256).hexdigest()
                if row is not None:
                    return hmac.compare_digest(row.disclosure_hmac,fingerprint)
                s.add(InstitutionalAnalyticsLiveReleaseRow(
                    institution_id=i,scope_key=scope_key,scope_json=scope_json,
                    nonce=nonce,disclosure_hmac=fingerprint,contract_version=1,
                    first_released_at=datetime.now(UTC)))
                try:
                    s.commit()
                    return True
                except IntegrityError:
                    s.rollback()  # simultaneous first release; re-read the winner
        return False

    def offering_ids(self,i,period_id=None,cohort_id=None):
        with self.sf() as s:
            q=select(OfferingRow.id).where(OfferingRow.institution_id==i)
            if period_id:q=q.where(OfferingRow.academic_period_id==period_id)
            if cohort_id:q=q.where(OfferingRow.cohort_id==cohort_id)
            return tuple(s.scalars(q).all())
    def distinct_active_students(self,i,period_id=None,cohort_id=None,offering_id=None,academic_unit_id=None):
        """Disclosure denominator: DISTINCT learners, not enrollment rows or attendance events.

        The offering/academic-unit boundaries come from tenant-scoped institutional
        records. A student enrolled in multiple cohorts contributes only once.
        """
        if academic_unit_id:
            cohorts=self.cohort_ids_for_unit(i,academic_unit_id,period_id)
        elif offering_id:
            with self.sf() as s:
                q=select(OfferingRow.cohort_id).where(OfferingRow.institution_id==i,OfferingRow.id==offering_id)
                if period_id:q=q.where(OfferingRow.academic_period_id==period_id)
                if cohort_id:q=q.where(OfferingRow.cohort_id==cohort_id)
                cohorts=tuple(s.scalars(q).all())
        else:
            with self.sf() as s:
                q=select(OfferingRow.cohort_id).where(OfferingRow.institution_id==i)
                if period_id:q=q.where(OfferingRow.academic_period_id==period_id)
                if cohort_id:q=q.where(OfferingRow.cohort_id==cohort_id)
                cohorts=tuple(s.scalars(q.distinct()).all())
        if not cohorts:return 0
        with self.sf() as s:
            valid_cohorts=select(CohortRow.id).where(
                CohortRow.institution_id==i,CohortRow.active==True,
                CohortRow.id.in_(cohorts))
            if period_id:
                valid_cohorts=valid_cohorts.where(CohortRow.academic_period_id==period_id)
            return int(s.scalar(select(func.count(func.distinct(EnrollmentRow.student_account_id))).where(
                EnrollmentRow.institution_id==i,EnrollmentRow.active==True,
                EnrollmentRow.cohort_id.in_(valid_cohorts))) or 0)

    def overlapping_cohort_disclosure_risk(self,i,period_id=None,cohort_id=None,
            offering_id=None,academic_unit_id=None,*,parent_population=None):
        """True if a releasable peer cohort differs from this audience by 1–2 people.

        Perform DISTINCT overlap arithmetic in SQL; never return student IDs or
        peer memberships to the application/API. This is a conservative, static
        peer-cohort guard (not protection against arbitrary cross-query attacks).
        Only active, offering-backed cohorts in the same institution and period
        are eligible peer views. Inactive/foreign enrollments cannot influence it.
        """
        if not any((cohort_id,offering_id,academic_unit_id)):
            return False
        if academic_unit_id:
            target_cohorts=self.cohort_ids_for_unit(i,academic_unit_id,period_id)
        elif offering_id:
            with self.sf() as s:
                q=select(OfferingRow.cohort_id,OfferingRow.academic_period_id).where(
                    OfferingRow.institution_id==i,OfferingRow.id==offering_id)
                row=s.execute(q).first()
            if not row or (period_id and row.academic_period_id!=period_id):return True
            target_cohorts=(row.cohort_id,)
            period_id=period_id or row.academic_period_id
        else:
            with self.sf() as s:
                row=s.execute(select(CohortRow.academic_period_id).where(
                    CohortRow.institution_id==i,CohortRow.id==cohort_id,
                    CohortRow.active==True)).first()
            if not row or (period_id and row.academic_period_id!=period_id):return True
            target_cohorts=(cohort_id,)
            period_id=period_id or row.academic_period_id
        if not target_cohorts:return False
        peer_offerings=select(OfferingRow.cohort_id).where(OfferingRow.institution_id==i)
        if period_id:peer_offerings=peer_offerings.where(OfferingRow.academic_period_id==period_id)
        peer_cohorts=select(CohortRow.id).where(CohortRow.institution_id==i,
            CohortRow.active==True,CohortRow.id.in_(peer_offerings))
        if period_id:peer_cohorts=peer_cohorts.where(CohortRow.academic_period_id==period_id)
        with self.sf() as s:
            audience=(select(EnrollmentRow.student_account_id).where(
                EnrollmentRow.institution_id==i,EnrollmentRow.active==True,
                EnrollmentRow.cohort_id.in_(target_cohorts)).distinct().subquery())
            members=(select(EnrollmentRow.cohort_id,EnrollmentRow.student_account_id).where(
                EnrollmentRow.institution_id==i,EnrollmentRow.active==True,
                EnrollmentRow.cohort_id.in_(peer_cohorts)).distinct().subquery())
            matched=members.outerjoin(audience,
                members.c.student_account_id==audience.c.student_account_id)
            counts=s.execute(select(members.c.cohort_id,
                func.count().label('size'),
                func.count(audience.c.student_account_id).label('intersection'))
                .select_from(matched).group_by(members.c.cohort_id)).all()
            target_size=int(s.scalar(select(func.count()).select_from(audience)) or 0)
            if parent_population is None:
                parent_population=self.distinct_active_students(i,period_id)
        if type(parent_population) is not int or target_size>parent_population:
            return True  # incoherent membership: no statistical release
        for _,peer_size,intersection in counts:
            if peer_size>parent_population or intersection>min(target_size,peer_size):
                return True  # contradictory populations must fail closed
            if peer_size<3 or intersection==0:
                continue
            peer_complement=parent_population-peer_size
            # A peer whose own release would be blocked by the parent
            # complement rule cannot be used to derive this difference.
            if peer_complement not in (0,) and peer_complement<3:
                continue
            only_target=target_size-intersection
            only_peer=peer_size-intersection
            if (0<only_target<3) or (0<only_peer<3):
                return True
        return False

    def period_population_overlap(self,i,previous_period_id,current_period_id,academic_unit_id=None):
        """Only return an overlap count to the service, never learner identities.

        SQL-side DISTINCT and institution predicates prevent duplicate records
        and foreign-tenant rows from inflating or hiding overlap.
        """
        program_ids=(self.descendant_program_ids(i,academic_unit_id)
                     if academic_unit_id else None)
        if academic_unit_id and not program_ids:return 0

        def cohort_scope(pid):
            q=select(CohortRow.id).where(CohortRow.institution_id==i,
                CohortRow.active==True,CohortRow.academic_period_id==pid)
            if academic_unit_id:
                return q.where(CohortRow.program_unit_id.in_(program_ids))
            offers=select(OfferingRow.cohort_id).where(
                OfferingRow.institution_id==i,OfferingRow.academic_period_id==pid)
            return q.where(CohortRow.id.in_(offers))

        def population(pid):
            return (select(EnrollmentRow.student_account_id)
                .where(EnrollmentRow.institution_id==i,EnrollmentRow.active==True,
                    EnrollmentRow.cohort_id.in_(cohort_scope(pid)))
                .distinct().subquery())

        with self.sf() as session:
            previous=population(previous_period_id)
            current=population(current_period_id)
            return int(session.scalar(select(func.count()).select_from(
                previous.join(current,previous.c.student_account_id==current.c.student_account_id))) or 0)

    def snapshot(self,i,period_id=None,cohort_id=None,offering_id=None,offering_ids=None,academic_unit_id=None,governed=False):
        ids=tuple(offering_ids) if offering_ids is not None else ((offering_id,) if offering_id else self.offering_ids(i,period_id,cohort_id))
        if not ids:return self._empty(i,period_id,cohort_id,offering_id)
        with self.sf() as s:
            offerings=s.scalars(select(OfferingRow).where(OfferingRow.institution_id==i,OfferingRow.id.in_(ids))).all()
            cohort_ids={x.cohort_id for x in offerings}
            # For Phase-15 governed decisions, an event is eligible only if its
            # learner is actively enrolled in the correct institutional cohort.
            # Legacy Lot-27 snapshots retain their original versioned semantics.
            eligible={c:set() for c in cohort_ids}
            if governed and cohort_ids:
                for e in s.scalars(select(EnrollmentRow).where(
                        EnrollmentRow.institution_id==i,EnrollmentRow.active==True,
                        EnrollmentRow.cohort_id.in_(cohort_ids))).all():
                    eligible[e.cohort_id].add(e.student_account_id)
            off_cohort={o.id:o.cohort_id for o in offerings}
            enrolled=int(s.scalar(select(func.count()).select_from(EnrollmentRow).where(EnrollmentRow.institution_id==i,EnrollmentRow.cohort_id.in_(cohort_ids),EnrollmentRow.active==True)) or 0)
            sessions=s.scalars(select(SessionRow).where(SessionRow.institution_id==i,SessionRow.offering_id.in_(ids))).all()
            valid_sessions=[x for x in sessions if x.state!='cancelled']; completed=sum(x.state=='completed' for x in valid_sessions)
            at_sessions=s.scalars(select(AttendanceSessionRow.id).where(AttendanceSessionRow.institution_id==i,AttendanceSessionRow.offering_id.in_(ids),AttendanceSessionRow.state=='closed')).all()
            recs=s.scalars(select(AttendanceRecordRow).where(AttendanceRecordRow.attendance_session_id.in_(at_sessions),
                *((AttendanceRecordRow.institution_id==i,) if governed else ()))).all() if at_sessions else []
            if governed:
                sid_off={x.id:x.offering_id for x in s.scalars(select(AttendanceSessionRow).where(
                    AttendanceSessionRow.id.in_(at_sessions),AttendanceSessionRow.institution_id==i)).all()}
                recs=[r for r in recs if r.student_account_id in eligible.get(off_cohort.get(sid_off.get(r.attendance_session_id)),set()) and r.review=='clear']
            ast=defaultdict(int)
            attendance_source_trusted=(not governed or all(
                r.status in ('present','late','absent','justified') for r in recs))
            for r in recs:ast[r.status]+=1
            assignments=s.scalars(select(AssignmentRow).where(AssignmentRow.institution_id==i,AssignmentRow.offering_id.in_(ids),AssignmentRow.state.in_(['published','closed','grading','results_published']))).all()
            submissions=s.scalars(select(SubmissionRow).where(SubmissionRow.institution_id==i,SubmissionRow.assignment_id.in_([a.id for a in assignments]),SubmissionRow.state.in_(['submitted','late','returned','graded']))).all() if assignments else []
            if governed:
                a_off={a.id:a.offering_id for a in assignments}
                submissions=[sub for sub in submissions if sub.student_account_id in
                  eligible.get(off_cohort.get(a_off.get(sub.assignment_id)),set())]
            unique_sub={(x.assignment_id,x.student_account_id) for x in submissions}
            opportunities=0
            enrollment_by_cohort={c: (len(eligible[c]) if governed else int(s.scalar(select(func.count()).select_from(EnrollmentRow).where(EnrollmentRow.cohort_id==c,EnrollmentRow.active==True)) or 0)) for c in cohort_ids}
            for a in assignments:opportunities+=enrollment_by_cohort.get(off_cohort.get(a.offering_id),0)
            gbs=s.scalars(select(GradebookRow).where(GradebookRow.institution_id==i,GradebookRow.offering_id.in_(ids))).all()
            complete=passed=0; student_results=[]; result_accounts=set()
            # Fail closed if any published, tenant-owned gradebook contains an
            # invalid scoring contract or contradictory validated marks.
            result_source_trusted=True
            for g in gbs:
                if governed and g.state!='published':continue
                comps=s.scalars(select(ComponentRow).where(ComponentRow.gradebook_id==g.id, *((ComponentRow.institution_id==i,) if governed else ()))).all()
                if not comps:
                    if governed:result_source_trusted=False
                    continue
                if not governed:
                    # Lot-27/legacy projections retain their prior published
                    # contract; Phase-15 hardening applies only to governed
                    # observatory queries, not historical archived dashboards.
                    legacy_marks=s.scalars(select(MarkRow).where(MarkRow.gradebook_id==g.id,
                        MarkRow.state=='validated')).all()
                    legacy_by=defaultdict(dict)
                    for mark in legacy_marks:legacy_by[mark.student_account_id][mark.component_id]=mark
                    for stu,mm in legacy_by.items():
                        if not all(c.id in mm for c in comps):continue
                        if any(mm[c.id].attendance in ('justified_absence','exempt') or mm[c.id].score is None for c in comps):continue
                        total=0.0
                        for c in comps:
                            mark=mm[c.id]
                            score=0.0 if mark.attendance=='absent' else float(mark.score)
                            total+=(score/float(c.max_score)*100)*(float(c.weight_percent)/100)
                        complete+=1;result_accounts.add(stu)
                        ok=total>=float(g.pass_percent)
                        passed+=int(ok);student_results.append((stu,total,ok))
                    continue
                # The gradebook is considered unverifiable when its grading
                # contract is corrupted. It is not silently omitted to improve
                # the published pass rate of other students.
                valid_contract=(isfinite(float(g.pass_percent)) and 0<=g.pass_percent<=100
                    and all(isfinite(float(c.max_score)) and float(c.max_score)>0 and
                            isfinite(float(c.weight_percent)) and float(c.weight_percent)>0 and
                            c.institution_id==i and c.gradebook_id==g.id for c in comps)
                    and abs(sum(float(c.weight_percent) for c in comps)-100)<0.01)
                if not valid_contract:
                    if governed:result_source_trusted=False
                    continue
                marks=s.scalars(select(MarkRow).where(MarkRow.gradebook_id==g.id,MarkRow.state=='validated',
                    *((MarkRow.institution_id==i,) if governed else ()))).all()
                if governed:
                    marks=[mark for mark in marks if mark.student_account_id in eligible.get(off_cohort.get(g.offering_id),set())]
                by=defaultdict(dict)
                contradictory=False
                components={c.id:c for c in comps}
                for mark in marks:
                    # Prevent foreign components, duplicated mark rows or invalid
                    # scores from being reinterpreted as a legitimate grade.
                    comp=components.get(mark.component_id)
                    if not comp or mark.institution_id!=i or mark.gradebook_id!=g.id:
                        contradictory=True;continue
                    if mark.component_id in by[mark.student_account_id]:
                        contradictory=True;continue
                    if (mark.attendance not in ('present','absent','justified_absence','exempt') or
                        (mark.attendance=='present' and
                         (mark.score is None or not isfinite(float(mark.score)) or
                          not 0<=float(mark.score)<=float(comp.max_score))) or
                        (mark.attendance=='absent' and mark.score is not None and
                         (not isfinite(float(mark.score)) or float(mark.score)!=0))):
                        contradictory=True;continue
                    by[mark.student_account_id][mark.component_id]=mark
                if contradictory:
                    if governed:result_source_trusted=False
                    continue
                for stu, mm in by.items():
                    if not all(c.id in mm for c in comps):continue
                    if any(mm[c.id].attendance in ('justified_absence','exempt') or mm[c.id].score is None for c in comps):continue
                    total=0.0
                    for c in comps:
                        mark=mm[c.id];score=0.0 if mark.attendance=='absent' else float(mark.score)
                        total+=(score/float(c.max_score)*100)*(float(c.weight_percent)/100)
                    complete+=1;result_accounts.add(stu);ok=total>=float(g.pass_percent);passed+=int(ok);student_results.append((stu,total,ok))
            topics=s.scalars(select(TopicRow).join(SyllabusRow,TopicRow.syllabus_id==SyllabusRow.id).where(SyllabusRow.institution_id==i,SyllabusRow.offering_id.in_(ids))).all()
            taught=sum(t.state=='taught' for t in topics); topic_total=sum(t.state!='skipped' for t in topics)
            total_att=sum(ast.values()); present=ast['present']+ast['late']
            # Internal-only disclosure metadata: repeated sessions or multiple
            # gradebooks for one student do not create three distinct people.
            contributors={'attendance.attendance_rate':len({r.student_account_id for r in recs}),
                          'assignments.submission_rate':len({student for _,student in unique_sub}),
                          'results.pass_rate':len(result_accounts)} if governed else {}
            return {'_source_integrity':{'results.pass_rate':result_source_trusted,
                'attendance.attendance_rate':attendance_source_trusted},'_metric_contributors':contributors,'institution_id':i,'scope':{'academic_period_id':period_id,'academic_unit_id':academic_unit_id,'cohort_id':cohort_id,'offering_id':offering_id},'population':{'active_enrollments':enrolled,'offerings':len(offerings)},'teaching':{'sessions_total':len(valid_sessions),'sessions_completed':completed,'completion_rate':self.pct(completed,len(valid_sessions)),'topics_total':topic_total,'topics_taught':taught,'syllabus_coverage_rate':self.pct(taught,topic_total)},'attendance':{'records':total_att,'present':ast['present'],'late':ast['late'],'absent':ast['absent'],'justified':ast['justified'],'attendance_rate':self.pct(present,total_att),'absence_rate':self.pct(ast['absent'],total_att)},'assignments':{'assignments':len(assignments),'submission_opportunities':opportunities,'submitted':len(unique_sub),'submission_rate':self.pct(len(unique_sub),opportunities)},'results':{'complete_results':complete,'passed':passed,'pass_rate':self.pct(passed,complete)},'_student_results':student_results}

    def pedagogical_intelligence(self,i,period_id=None,cohort_id=None,offering_id=None,offering_ids=None):
        ids=tuple(offering_ids) if offering_ids is not None else ((offering_id,) if offering_id else self.offering_ids(i,period_id,cohort_id))
        if not ids:return {'assessment':{'attempts':0,'average_percent':None,'pass_rate':None,'by_bloom':{}},'knowledge_graph':{'published_concepts':0,'published_relations':0,'courses_covered':0}}
        with self.sf() as s:
            offs=s.scalars(select(OfferingRow).where(OfferingRow.institution_id==i,OfferingRow.id.in_(ids))).all(); courses=tuple({x.course_id for x in offs})
            bps=s.scalars(select(BlueprintRow).where(BlueprintRow.course_id.in_(courses))).all() if courses else []; bpids=[x.id for x in bps]
            attempts=s.scalars(select(AttemptRow).where(AttemptRow.blueprint_id.in_(bpids),AttemptRow.state=='submitted')).all() if bpids else []; aids=[x.id for x in attempts]
            results=s.scalars(select(ResultRow).where(ResultRow.attempt_id.in_(aids))).all() if aids else []
            bloom_sum=defaultdict(float); bloom_n=defaultdict(int)
            for r in results:
                for k,v in (r.by_bloom or {}).items():
                    if isinstance(v,(int,float)): bloom_sum[k]+=float(v); bloom_n[k]+=1
            by_bloom={k:round(bloom_sum[k]/bloom_n[k],2) for k in sorted(bloom_sum)}
            avg=round(sum(r.percent for r in results)/len(results),2) if results else None
            passed=sum(bool(r.passed) for r in results)
            nodes=s.scalars(select(NodeRow).where(NodeRow.tenant_id==i,NodeRow.course_id.in_(courses),NodeRow.state=='published')).all() if courses else []
            node_ids=[x.id for x in nodes]
            rels=s.scalars(select(RelationRow).where(RelationRow.tenant_id==i,RelationRow.state=='published',RelationRow.source_id.in_(node_ids),RelationRow.target_id.in_(node_ids))).all() if node_ids else []
            return {'assessment':{'attempts':len(results),'average_percent':avg,'pass_rate':self.pct(passed,len(results)),'by_bloom':by_bloom},'knowledge_graph':{'published_concepts':len(nodes),'published_relations':len(rels),'courses_covered':len({x.course_id for x in nodes if x.course_id})}}
    @staticmethod
    def pct(n,d):return round(n/d*100,2) if d else None
    @staticmethod
    def _empty(i,p,c,o):return {'institution_id':i,'scope':{'academic_period_id':p,'academic_unit_id':None,'cohort_id':c,'offering_id':o},'population':{'active_enrollments':0,'offerings':0},'teaching':{'sessions_total':0,'sessions_completed':0,'completion_rate':None,'topics_total':0,'topics_taught':0,'syllabus_coverage_rate':None},'attendance':{'records':0,'present':0,'late':0,'absent':0,'justified':0,'attendance_rate':None,'absence_rate':None},'assignments':{'assignments':0,'submission_opportunities':0,'submitted':0,'submission_rate':None},'results':{'complete_results':0,'passed':0,'pass_rate':None},'_student_results':[]}
