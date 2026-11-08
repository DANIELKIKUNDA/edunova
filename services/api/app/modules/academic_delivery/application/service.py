from uuid import uuid4
import hashlib, json
from app.modules.academic_delivery.domain.model import OfferingCurriculumLink, PublishedCourseResult
from app.modules.academic_catalog.domain.model import CurriculumState
from app.modules.campus.domain.model import CampusRole, MembershipState, PeriodKind
from app.modules.student_records.domain.model import RegistrationState, CourseRegistrationState, StudentState

ADMIN={CampusRole.OWNER,CampusRole.RECTOR,CampusRole.ADMIN,CampusRole.ACADEMIC_ADMIN,CampusRole.FACULTY_ADMIN}
class AcademicDeliveryService:
    def __init__(self,repo,campus,teaching,academic,students,now,audit=None):
        self.repo=repo;self.campus=campus;self.teaching=teaching;self.academic=academic;self.students=students;self.now=now;self.audit=audit
    def _audit(self,a,action,target,id,meta=None):
        if self.audit:self.audit.record(actor_id=a,action=action,target_type=target,target_id=id,metadata=meta or {})
    def _member(self,a,i):
        m=self.campus.membership(i,a)
        if not m or m.state!=MembershipState.ACTIVE:raise PermissionError('academic_delivery_membership_required')
        return m
    def bind_offering(self,a,i,offering_id,curriculum_course_id):
        m=self._member(a,i)
        if m.role not in ADMIN:raise PermissionError('academic_delivery_admin_required')
        off=self.teaching.offering(i,offering_id)
        if not off:raise ValueError('academic_delivery_offering_not_found')
        binding=self.academic.binding_for_cohort(i,off.cohort_id)
        if not binding:raise ValueError('academic_delivery_cohort_curriculum_required')
        curriculum=self.academic.curriculum(i,binding.curriculum_id)
        if not curriculum or curriculum.state!=CurriculumState.PUBLISHED:raise ValueError('academic_delivery_published_curriculum_required')
        course=next((c for c in self.academic.courses(curriculum.id) if c.id==curriculum_course_id),None)
        if not course:raise ValueError('academic_delivery_course_not_in_cohort_curriculum')
        cohort=self.campus.cohort(i,off.cohort_id);period=self.campus.period(i,off.academic_period_id)
        if not cohort or not period:raise ValueError('academic_delivery_invalid_scope')
        if cohort.program_unit_id!=curriculum.program_unit_id:raise ValueError('academic_delivery_program_mismatch')
        # Offering period must belong to the curriculum academic year, directly or through a semester/term parent.
        period_year=period.id if period.kind==PeriodKind.ACADEMIC_YEAR else period.parent_id
        if period_year!=curriculum.effective_academic_year_id:raise ValueError('academic_delivery_academic_year_mismatch')
        old=self.repo.link_for_offering(i,offering_id)
        if old and old.curriculum_course_id!=curriculum_course_id:raise ValueError('academic_delivery_offering_already_bound')
        if old:return old
        x=OfferingCurriculumLink(uuid4().hex,i,offering_id,curriculum.id,curriculum_course_id,off.cohort_id,a,self.now());self.repo.save_link(x)
        self._audit(a,'academic_delivery.offering.bound','teaching_offering',offering_id,{'curriculum_course_id':curriculum_course_id})
        return x
    def assert_student_eligible(self,account_id,i,offering_id):
        link=self.repo.link_for_offering(i,offering_id)
        if not link:raise ValueError('academic_delivery_offering_unbound')
        student=self.students.by_account(i,account_id)
        if not student or student.state!=StudentState.ACTIVE:raise PermissionError('academic_delivery_active_student_required')
        if student.cohort_id!=link.cohort_id or student.curriculum_id!=link.curriculum_id:raise PermissionError('academic_delivery_student_scope_mismatch')
        regs=[r for r in self.students.registrations(student.id) if r.cohort_id==link.cohort_id and r.curriculum_id==link.curriculum_id and r.state==RegistrationState.ENROLLED]
        if not regs:raise PermissionError('academic_delivery_active_registration_required')
        cr=self.repo.course_registration(student.id,link.curriculum_course_id)
        if not cr or cr.registration_id not in {r.id for r in regs}:raise PermissionError('academic_delivery_course_registration_required')
        if cr.state not in {CourseRegistrationState.ENROLLED,CourseRegistrationState.FAILED}:raise PermissionError('academic_delivery_course_not_active')
        return cr
    def record_published_result(self,a,i,offering_id,student_account_id,*,passed,complete,published,gradebook_id=None,percent=None,components=()):
        if not complete or not published:raise ValueError('academic_delivery_final_result_required')
        cr=self.assert_student_eligible(student_account_id,i,offering_id)
        target=CourseRegistrationState.VALIDATED if passed else CourseRegistrationState.FAILED
        self.repo.set_course_registration_state(cr.id,target)
        if gradebook_id is not None:
            if percent is None or not 0<=float(percent)<=100:raise ValueError('academic_delivery_published_percent_required')
            payload={'course_registration_id':cr.id,'curriculum_course_id':cr.curriculum_course_id,'offering_id':offering_id,'gradebook_id':gradebook_id,'percent':round(float(percent),2),'passed':bool(passed),'components':list(components)}
            evidence=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            x=PublishedCourseResult(uuid4().hex,i,cr.student_id,student_account_id,cr.id,cr.curriculum_course_id,offering_id,gradebook_id,round(float(percent),2),bool(passed),evidence,a,self.now())
            self.repo.save_published_result(x)
        self._audit(a,'academic_delivery.course_result.recorded','student_course_registration',cr.id,{'state':target.value,'offering_id':offering_id,'gradebook_id':gradebook_id})
        return target
