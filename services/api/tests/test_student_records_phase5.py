import pytest
from app.runtime import runtime
from app.modules.campus.domain.model import UnitKind,PeriodKind,CampusRole
from test_phase4_max_depth import complete_review

def admitted_student(seed='student5'):
 admin,inst,app,r=complete_review(seed);r=runtime.admission_center.decide(admin,inst.id,r.id,r.row_version,'admitted');campaign=runtime.admissions_catalog_repo.campaign_any(app.campaign_id);program=runtime.campus_repo.unit(inst.id,campaign.program_unit_id);year=runtime.campus_repo.period(inst.id,campaign.academic_year_id);co=runtime.campus.create_cohort(admin,inst.id,program_unit_id=program.id,academic_period_id=year.id,name='Promotion '+seed,level='BAC1');runtime.academic_catalog.bind_cohort(admin,inst.id,campaign.curriculum_id,co.id);s=runtime.student_records.matriculate(admin,inst.id,r.id,co.id);return admin,inst,app,r,co,s

def test_admitted_candidate_becomes_student_with_matricule_membership_registration():
 admin,inst,app,r,co,s=admitted_student('matricule');assert s.matricule and s.account_id==app.account_id and s.curriculum_id
 m=runtime.campus_repo.membership(inst.id,app.account_id);assert m.role==CampusRole.STUDENT and m.state.value=='active'
 regs=runtime.student_record_repo.registrations(s.id);assert len(regs)==1 and regs[0].cohort_id==co.id
 assert runtime.student_records.matriculate(admin,inst.id,r.id,co.id).id==s.id

def test_non_admitted_review_cannot_be_matriculated():
 admin,inst,app,r=complete_review('notadmitted');campaign=runtime.admissions_catalog_repo.campaign_any(app.campaign_id);year=runtime.campus_repo.period(inst.id,campaign.academic_year_id);co=runtime.campus.create_cohort(admin,inst.id,program_unit_id=campaign.program_unit_id,academic_period_id=year.id,name='P',level='BAC1');runtime.academic_catalog.bind_cohort(admin,inst.id,campaign.curriculum_id,co.id)
 with pytest.raises(ValueError,match='admitted_review_required'):runtime.student_records.matriculate(admin,inst.id,r.id,co.id)

def test_wrong_cohort_or_unbound_curriculum_is_rejected():
 admin,inst,app,r=complete_review('wrongco');r=runtime.admission_center.decide(admin,inst.id,r.id,r.row_version,'admitted');campaign=runtime.admissions_catalog_repo.campaign_any(app.campaign_id);year=runtime.campus_repo.period(inst.id,campaign.academic_year_id);co=runtime.campus.create_cohort(admin,inst.id,program_unit_id=campaign.program_unit_id,academic_period_id=year.id,name='Unbound',level='BAC1')
 with pytest.raises(ValueError,match='curriculum_mismatch'):runtime.student_records.matriculate(admin,inst.id,r.id,co.id)

def test_student_can_only_read_own_dossier_and_admin_can_change_lifecycle():
 admin,inst,app,r,co,s=admitted_student('privacy5');mine=runtime.student_records.my_dossier(app.account_id,inst.id);assert mine['student'].id==s.id
 _,inst2,app2,r2,co2,s2=admitted_student('privacy-other')
 with pytest.raises((ValueError,PermissionError)):runtime.student_records.dossier(app.account_id,inst2.id,s2.id)
 y=runtime.student_records.change_state(admin,inst.id,s.id,s.row_version,'suspended','disciplinary hold');assert y.state.value=='suspended'
 y=runtime.student_records.change_state(admin,inst.id,s.id,y.row_version,'active','cleared');assert y.state.value=='active' and len(runtime.student_record_repo.events(s.id))==3

def test_matricules_are_unique_sequential_within_institution_year():
 admin,inst,app,r,co,s1=admitted_student('seq1')
 # second candidate same campaign/cohort
 from test_candidate_applications_phase3 import consent
 a2='seq2';x=runtime.applications.create(a2,app.campaign_id,given_names='Second',family_name='Student');d=runtime.applications.upload(a2,x.id,'DIPLOME','d.pdf','application/pdf',b'%PDF-1.4\nseq2');consent(a2,x.id);x=runtime.applications.submit(a2,x.id,x.row_version);rr=runtime.admission_center.intake(admin,inst.id,x.id);runtime.admission_center.review_document(admin,inst.id,rr.id,d.id,'accepted');rr=runtime.admission_center.mark_complete(admin,inst.id,rr.id,rr.row_version);rr=runtime.admission_center.decide(admin,inst.id,rr.id,rr.row_version,'admitted');s2=runtime.student_records.matriculate(admin,inst.id,rr.id,co.id);assert s1.matricule!=s2.matricule and s2.matricule.endswith('000002')

def test_curriculum_courses_are_snapshotted_and_reenrollment_is_idempotent():
 from datetime import date
 admin,inst,app,r,co,s=admitted_student('reenroll');courses=runtime.student_record_repo.course_registrations(s.id);assert len(courses)==131 and {x.semester for x in courses}==set(range(1,15))
 reg0=runtime.student_record_repo.registrations(s.id)[0];runtime.student_records.change_registration_state(admin,inst.id,s.id,reg0.id,reg0.row_version,'completed','Annual progression validated');campaign=runtime.admissions_catalog_repo.campaign_any(app.campaign_id);y2=runtime.campus.add_period(admin,inst.id,kind=PeriodKind.ACADEMIC_YEAR,name='2028-2029',starts_on=date(2028,9,1),ends_on=date(2029,7,31));co2=runtime.campus.create_cohort(admin,inst.id,program_unit_id=campaign.program_unit_id,academic_period_id=y2.id,name='Promotion suivante',level='BAC2');runtime.academic_catalog.bind_cohort(admin,inst.id,campaign.curriculum_id,co2.id);reg=runtime.student_records.register_academic_year(admin,inst.id,s.id,co2.id);same=runtime.student_records.register_academic_year(admin,inst.id,s.id,co2.id);assert same.id==reg.id and len(runtime.student_record_repo.registrations(s.id))==2 and len(runtime.student_record_repo.course_registrations(s.id))==262
