from datetime import date
import pytest
from app.runtime import runtime
from app.modules.campus.domain.model import UnitKind,PeriodKind

def setup():
 a='phase1-owner-'+__import__('uuid').uuid4().hex;i=runtime.campus.create_institution(a,name='Université Phase 1',slug='phase1-'+__import__('uuid').uuid4().hex);f=runtime.campus.add_unit(a,i.id,kind=UnitKind.FACULTY,name='Faculté de Médecine',code='FM'+i.id[:5]);p=runtime.campus.add_unit(a,i.id,kind=UnitKind.PROGRAM,name='Médecine',code='MED'+i.id[:5],parent_id=f.id);y=runtime.campus.add_period(a,i.id,kind=PeriodKind.ACADEMIC_YEAR,name='2026-2027',starts_on=date(2026,10,1),ends_on=date(2027,7,31));return a,i,p,y

def test_medicine_becomes_versioned_institutional_curriculum():
 a,i,p,y=setup();c=runtime.academic_catalog.create(a,i.id,program_unit_id=p.id,effective_academic_year_id=y.id,code='MED-LMD',title='Doctorat en médecine',source_catalog_id='medicine_2025_2026');rows=runtime.academic_catalog.import_medicine(a,i.id,c.id);assert len(rows)==131;assert {x.semester for x in rows}==set(range(1,15));pub=runtime.academic_catalog.publish(a,i.id,c.id,1);assert pub.state.value=='published'
def test_version_duplicate_rejected():
 a,i,p,y=setup();runtime.academic_catalog.create(a,i.id,program_unit_id=p.id,effective_academic_year_id=y.id,code='MED',title='Médecine',version=1)
 with pytest.raises(ValueError,match='version_exists'):runtime.academic_catalog.create(a,i.id,program_unit_id=p.id,effective_academic_year_id=y.id,code='MED2',title='Médecine 2',version=1)
def test_prerequisite_cycle_is_rejected():
 a,i,p,y=setup();c=runtime.academic_catalog.create(a,i.id,program_unit_id=p.id,effective_academic_year_id=y.id,code='MED',title='Médecine');rows=runtime.academic_catalog.import_medicine(a,i.id,c.id);x,yc=rows[0],rows[1];runtime.academic_catalog.add_prerequisite(a,i.id,c.id,course_id=yc.id,required_course_id=x.id)
 with pytest.raises(ValueError,match='prerequisite_cycle'):runtime.academic_catalog.add_prerequisite(a,i.id,c.id,course_id=x.id,required_course_id=yc.id)
def test_published_curriculum_is_immutable_for_prerequisites():
 a,i,p,y=setup();c=runtime.academic_catalog.create(a,i.id,program_unit_id=p.id,effective_academic_year_id=y.id,code='MED',title='Médecine');rows=runtime.academic_catalog.import_medicine(a,i.id,c.id);runtime.academic_catalog.publish(a,i.id,c.id,1)
 with pytest.raises(ValueError,match='not_editable'):runtime.academic_catalog.add_prerequisite(a,i.id,c.id,course_id=rows[1].id,required_course_id=rows[0].id)
def test_curriculum_is_tenant_isolated():
 a,i,p,y=setup();c=runtime.academic_catalog.create(a,i.id,program_unit_id=p.id,effective_academic_year_id=y.id,code='MED',title='Médecine');b,j,_,_=setup()
 with pytest.raises(PermissionError):runtime.academic_catalog.detail(b,i.id,c.id)
 with pytest.raises(ValueError,match='not_found'):runtime.academic_catalog.detail(b,j.id,c.id)
