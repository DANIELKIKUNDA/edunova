import pytest
from app.runtime import runtime
from test_student_records_phase5 import admitted_student

def test_identity_correction_is_versioned_reasoned_and_audited():
 admin,inst,app,r,co,s=admitted_student('identitydeep');y=runtime.student_records.correct_identity(admin,inst.id,s.id,s.row_version,'Legal spelling correction',family_name='Corrected')
 assert y.family_name=='Corrected' and y.row_version==s.row_version+1
 h=runtime.student_record_repo.administrative_history(s.id);assert len(h)==1 and h[0].action_type=='identity_correction' and 'family_name' in h[0].before_json
 with pytest.raises(ValueError,match='concurrent_modification'):runtime.student_records.correct_identity(admin,inst.id,s.id,s.row_version,'stale edit',family_name='Bad')

def test_registration_lifecycle_requires_reason_and_blocks_premature_reenrollment():
 from datetime import date
 from app.modules.campus.domain.model import PeriodKind
 admin,inst,app,r,co,s=admitted_student('regdeep');reg=runtime.student_record_repo.registrations(s.id)[0]
 campaign=runtime.admissions_catalog_repo.campaign_any(app.campaign_id);y2=runtime.campus.add_period(admin,inst.id,kind=PeriodKind.ACADEMIC_YEAR,name='2028-2029',starts_on=date(2028,9,1),ends_on=date(2029,7,31));co2=runtime.campus.create_cohort(admin,inst.id,program_unit_id=campaign.program_unit_id,academic_period_id=y2.id,name='Next',level='BAC2');runtime.academic_catalog.bind_cohort(admin,inst.id,campaign.curriculum_id,co2.id)
 with pytest.raises(ValueError,match='previous_registration_must_be_closed'):runtime.student_records.register_academic_year(admin,inst.id,s.id,co2.id)
 with pytest.raises(ValueError,match='reason_required'):runtime.student_records.change_registration_state(admin,inst.id,s.id,reg.id,reg.row_version,'completed','')
 closed=runtime.student_records.change_registration_state(admin,inst.id,s.id,reg.id,reg.row_version,'completed','Annual jury validated progression');assert closed.state.value=='completed'
 reg2=runtime.student_records.register_academic_year(admin,inst.id,s.id,co2.id);assert reg2.academic_year_id==y2.id

def test_registration_transition_is_terminal_and_optimistically_locked():
 admin,inst,app,r,co,s=admitted_student('lockdeep');reg=runtime.student_record_repo.registrations(s.id)[0];x=runtime.student_records.change_registration_state(admin,inst.id,s.id,reg.id,reg.row_version,'suspended','Approved study leave')
 with pytest.raises(ValueError,match='concurrent_modification'):runtime.student_records.change_registration_state(admin,inst.id,s.id,reg.id,reg.row_version,'enrolled','stale')
 y=runtime.student_records.change_registration_state(admin,inst.id,s.id,x.id,x.row_version,'withdrawn','Student requested withdrawal');assert y.state.value=='withdrawn'
 with pytest.raises(ValueError,match='invalid_registration_transition'):runtime.student_records.change_registration_state(admin,inst.id,s.id,y.id,y.row_version,'enrolled','cannot reopen terminal state')
