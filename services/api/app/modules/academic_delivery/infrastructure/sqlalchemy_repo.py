from sqlalchemy import String, DateTime, UniqueConstraint, select, update, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.infrastructure.database import Base
from app.modules.academic_delivery.domain.model import OfferingCurriculumLink, PublishedCourseResult
from app.modules.student_records.infrastructure.sqlalchemy_repo import StudentCourseRegistrationRow
from app.modules.student_records.domain.model import StudentCourseRegistration, CourseRegistrationState

class OfferingCurriculumLinkRow(Base):
    __tablename__ = 'academic_delivery_offering_links'
    __table_args__ = (UniqueConstraint('offering_id', name='uq_academic_delivery_offering'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(64), index=True)
    offering_id: Mapped[str] = mapped_column(String(64), index=True)
    curriculum_id: Mapped[str] = mapped_column(String(64), index=True)
    curriculum_course_id: Mapped[str] = mapped_column(String(64), index=True)
    cohort_id: Mapped[str] = mapped_column(String(64), index=True)
    bound_by: Mapped[str] = mapped_column(String(64))
    bound_at: Mapped[object] = mapped_column(DateTime(timezone=True))


class PublishedCourseResultRow(Base):
    __tablename__ = 'academic_published_course_results'
    __table_args__ = (UniqueConstraint('course_registration_id', name='uq_academic_published_course_result_registration'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(64), index=True)
    student_id: Mapped[str] = mapped_column(String(64), index=True)
    student_account_id: Mapped[str] = mapped_column(String(64), index=True)
    course_registration_id: Mapped[str] = mapped_column(String(64), index=True)
    curriculum_course_id: Mapped[str] = mapped_column(String(64), index=True)
    offering_id: Mapped[str] = mapped_column(String(64), index=True)
    gradebook_id: Mapped[str] = mapped_column(String(64), index=True)
    percent: Mapped[float] = mapped_column(Float)
    passed: Mapped[bool] = mapped_column(Boolean)
    evidence_hash: Mapped[str] = mapped_column(String(64))
    published_by: Mapped[str] = mapped_column(String(64))
    published_at: Mapped[object] = mapped_column(DateTime(timezone=True), index=True)

class SqlAcademicDeliveryRepository:
    def __init__(self, sf): self.sf = sf
    def _x(self, r): return OfferingCurriculumLink(r.id,r.institution_id,r.offering_id,r.curriculum_id,r.curriculum_course_id,r.cohort_id,r.bound_by,r.bound_at)
    def link_for_offering(self, institution_id, offering_id):
        with self.sf() as s:
            r=s.scalar(select(OfferingCurriculumLinkRow).where(OfferingCurriculumLinkRow.institution_id==institution_id,OfferingCurriculumLinkRow.offering_id==offering_id))
            return self._x(r) if r else None
    def save_link(self, x):
        with self.sf() as s:
            old=s.scalar(select(OfferingCurriculumLinkRow).where(OfferingCurriculumLinkRow.offering_id==x.offering_id))
            if old:
                if old.institution_id!=x.institution_id: raise ValueError('academic_delivery_cross_tenant_link')
                old.curriculum_id=x.curriculum_id;old.curriculum_course_id=x.curriculum_course_id;old.cohort_id=x.cohort_id;old.bound_by=x.bound_by;old.bound_at=x.bound_at
            else:s.add(OfferingCurriculumLinkRow(**x.__dict__))
            s.commit()
    def course_registration(self, student_id, curriculum_course_id):
        with self.sf() as s:
            r=s.scalar(select(StudentCourseRegistrationRow).where(StudentCourseRegistrationRow.student_id==student_id,StudentCourseRegistrationRow.curriculum_course_id==curriculum_course_id))
            if not r:return None
            return StudentCourseRegistration(r.id,r.registration_id,r.student_id,r.curriculum_course_id,r.semester,r.course_code,r.course_title,float(r.credits) if r.credits is not None else None,CourseRegistrationState(r.state),r.created_at)
    def set_course_registration_state(self, registration_id, state):
        with self.sf() as s:
            r=s.execute(update(StudentCourseRegistrationRow).where(StudentCourseRegistrationRow.id==registration_id).values(state=state.value))
            if r.rowcount!=1:s.rollback();raise ValueError('academic_delivery_course_registration_not_found')
            s.commit()
    def _result(self, r):
        return PublishedCourseResult(r.id,r.institution_id,r.student_id,r.student_account_id,r.course_registration_id,r.curriculum_course_id,r.offering_id,r.gradebook_id,r.percent,r.passed,r.evidence_hash,r.published_by,r.published_at)
    def save_published_result(self, x):
        with self.sf() as s:
            old=s.scalar(select(PublishedCourseResultRow).where(PublishedCourseResultRow.course_registration_id==x.course_registration_id))
            if old:
                if old.institution_id!=x.institution_id or old.student_id!=x.student_id:raise ValueError('academic_delivery_published_result_scope_mismatch')
                # Publication is immutable. Idempotent retries are accepted, conflicting evidence is rejected.
                if old.gradebook_id!=x.gradebook_id or old.evidence_hash!=x.evidence_hash:raise ValueError('academic_delivery_published_result_already_recorded')
                return self._result(old)
            s.add(PublishedCourseResultRow(id=x.id,institution_id=x.institution_id,student_id=x.student_id,student_account_id=x.student_account_id,course_registration_id=x.course_registration_id,curriculum_course_id=x.curriculum_course_id,offering_id=x.offering_id,gradebook_id=x.gradebook_id,percent=x.percent,passed=x.passed,evidence_hash=x.evidence_hash,published_by=x.published_by,published_at=x.published_at));s.commit();return x
    def published_results(self, institution_id, student_id):
        with self.sf() as s:
            q=select(PublishedCourseResultRow).where(PublishedCourseResultRow.institution_id==institution_id,PublishedCourseResultRow.student_id==student_id).order_by(PublishedCourseResultRow.published_at,PublishedCourseResultRow.id)
            return tuple(self._result(r) for r in s.scalars(q).all())

