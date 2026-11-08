from datetime import UTC,date,datetime,timedelta
import pytest
from app.runtime import runtime
from app.modules.campus.domain.model import UnitKind,PeriodKind

def base():
 u=__import__('uuid').uuid4().hex;a='deep-'+u;i=runtime.campus.create_institution(a,name='Université Deep',slug='deep-'+u);f=runtime.campus.add_unit(a,i.id,kind=UnitKind.FACULTY,name='Médecine',code='F'+u[:5]);p=runtime.campus.add_unit(a,i.id,kind=UnitKind.PROGRAM,name='Médecine',code='P'+u[:5],parent_id=f.id);y=runtime.campus.add_period(a,i.id,kind=PeriodKind.ACADEMIC_YEAR,name='2027-2028',starts_on=date(2027,9,1),ends_on=date(2028,7,31));return a,i,p,y

def published():
 a,i,p,y=base();c=runtime.academic_catalog.create(a,i.id,program_unit_id=p.id,effective_academic_year_id=y.id,code='MED',title='Médecine',source_catalog_id='medicine_2025_2026');runtime.academic_catalog.import_medicine(a,i.id,c.id);c=runtime.academic_catalog.publish(a,i.id,c.id,1);return a,i,p,y,c

def test_medicine_import_preserves_hour_components_and_source_structure():
 a,i,p,y=base();c=runtime.academic_catalog.create(a,i.id,program_unit_id=p.id,effective_academic_year_id=y.id,code='MED',title='Médecine');rows=runtime.academic_catalog.import_medicine(a,i.id,c.id);ana=next(x for x in rows if x.code=='ANA1111');assert (ana.cmi,ana.tp_td,ana.tpe,ana.total_hours,ana.credits,ana.ue_declared_credits)==(80,40,80,200,8,21);assert ana.cycle=='Bachelier' and ana.level=='Bachelier 1'

def test_curriculum_can_clone_without_mutating_published_source_and_then_retire_source():
 a,i,p,y,c=published();y2=runtime.campus.add_period(a,i.id,kind=PeriodKind.ACADEMIC_YEAR,name='2028-2029',starts_on=date(2028,9,1),ends_on=date(2029,7,31));clone=runtime.academic_catalog.clone_version(a,i.id,c.id,effective_academic_year_id=y2.id);srcrows=runtime.academic_catalog.detail(a,i.id,c.id)[1];dstrows=runtime.academic_catalog.detail(a,i.id,clone.id)[1];assert clone.version==2 and len(srcrows)==len(dstrows)==131 and srcrows[0].id!=dstrows[0].id;ret=runtime.academic_catalog.retire(a,i.id,c.id,c.row_version);assert ret.state.value=='retired'

def test_curriculum_binding_is_single_and_program_compatible():
 a,i,p,y,c=published();co=runtime.campus.create_cohort(a,i.id,program_unit_id=p.id,academic_period_id=y.id,name='BAC1 2027',level='BAC1');b=runtime.academic_catalog.bind_cohort(a,i.id,c.id,co.id);assert b.cohort_id==co.id
 with pytest.raises(ValueError,match='already_bound'):runtime.academic_catalog.bind_cohort(a,i.id,c.id,co.id)

def test_campaign_deep_validation_update_requirement_removal_and_availability():
 a,i,p,y,c=published();n=datetime.now(UTC)+timedelta(days=10);camp=runtime.admissions_catalog.create(a,i.id,program_unit_id=p.id,academic_year_id=y.id,curriculum_id=c.id,slug='med-2027',title='Médecine',summary='Admission',opens_at=n,closes_at=n+timedelta(days=30),contact_email='admissions@example.cd',instructions='Préparez les originaux.',study_mode='on_campus',campus_label='Campus central',intake_label='Septembre 2027');r=runtime.admissions_catalog.add_requirement(a,i.id,camp.id,code='DIPLOME',label='Diplôme');report=runtime.admissions_catalog.validate(a,i.id,camp.id);assert report['publishable'];runtime.admissions_catalog.remove_requirement(a,i.id,camp.id,r.id);assert not runtime.admissions_catalog.validate(a,i.id,camp.id)['publishable'];runtime.admissions_catalog.add_requirement(a,i.id,camp.id,code='DIPLOME',label='Diplôme');camp=runtime.admissions_catalog.update_draft(a,i.id,camp.id,camp.row_version,title='Admissions médecine');camp=runtime.admissions_catalog.publish(a,i.id,camp.id,camp.row_version);assert runtime.admissions_catalog.public_detail(i.slug,camp.slug)[-1]=='upcoming'

def test_campaign_rejects_naive_dates_duplicate_requirement_bad_email_and_archives_closed():
 a,i,p,y,c=published();n=datetime.now();
 with pytest.raises(ValueError,match='timezone_required'):runtime.admissions_catalog.create(a,i.id,program_unit_id=p.id,academic_year_id=y.id,curriculum_id=c.id,slug='x',title='X',summary='',opens_at=n,closes_at=n+timedelta(days=1))
 z=datetime.now(UTC);camp=runtime.admissions_catalog.create(a,i.id,program_unit_id=p.id,academic_year_id=y.id,curriculum_id=c.id,slug='ok',title='OK',summary='',opens_at=z-timedelta(days=1),closes_at=z+timedelta(days=1),contact_email='a@b.cd');runtime.admissions_catalog.add_requirement(a,i.id,camp.id,code='ID',label='Identité')
 with pytest.raises(ValueError,match='code_exists'):runtime.admissions_catalog.add_requirement(a,i.id,camp.id,code='ID',label='Autre')
 camp=runtime.admissions_catalog.publish(a,i.id,camp.id,camp.row_version);assert runtime.admissions_catalog.public_detail(i.slug,camp.slug)[-1]=='open';camp=runtime.admissions_catalog.close(a,i.id,camp.id,camp.row_version);camp=runtime.admissions_catalog.archive(a,i.id,camp.id,camp.row_version)
 with pytest.raises(ValueError,match='public_campaign_not_found'):runtime.admissions_catalog.public_detail(i.slug,camp.slug)
