from datetime import UTC,date,datetime,timedelta
import pytest
from app.runtime import runtime
from app.modules.campus.domain.model import UnitKind,PeriodKind

def setup():
 u=__import__('uuid').uuid4().hex;a='phase2-'+u;i=runtime.campus.create_institution(a,name='Université Admissions '+u[:5],slug='ua-'+u);f=runtime.campus.add_unit(a,i.id,kind=UnitKind.FACULTY,name='Médecine',code='F'+u[:7]);p=runtime.campus.add_unit(a,i.id,kind=UnitKind.PROGRAM,name='Doctorat en médecine',code='M'+u[:7],parent_id=f.id);y=runtime.campus.add_period(a,i.id,kind=PeriodKind.ACADEMIC_YEAR,name='2027-2028',starts_on=date(2027,9,1),ends_on=date(2028,7,31));cur=runtime.academic_catalog.create(a,i.id,program_unit_id=p.id,effective_academic_year_id=y.id,code='MED',title='Médecine');runtime.academic_catalog.import_medicine(a,i.id,cur.id);cur=runtime.academic_catalog.publish(a,i.id,cur.id,1);return a,i,p,y,cur

def campaign(a,i,p,y,cur,slug='medecine-2027'):
 n=datetime(2027,5,1,tzinfo=UTC);return runtime.admissions_catalog.create(a,i.id,program_unit_id=p.id,academic_year_id=y.id,curriculum_id=cur.id,slug=slug,title='Admissions Médecine 2027-2028',summary='Candidatures ouvertes.',opens_at=n,closes_at=n+timedelta(days=120),capacity=300,application_fee_minor=1000,currency='USD',contact_email='admissions@example.cd')

def test_public_campaign_requires_explicit_publication_and_exposes_safe_catalog():
 a,i,p,y,cur=setup();c=campaign(a,i,p,y,cur)
 with pytest.raises(ValueError,match='public_campaign_not_found'):runtime.admissions_catalog.public_detail(i.slug,c.slug)
 runtime.admissions_catalog.add_requirement(a,i.id,c.id,code='DIPLOME',label='Diplôme ou attestation',required=True,document_required=True);runtime.admissions_catalog.publish(a,i.id,c.id,1)
 inst,program,year,curr,pub,reqs,status=runtime.admissions_catalog.public_detail(i.slug,c.slug);assert inst.id==i.id and program.id==p.id and curr.state.value=='published';assert pub.capacity==300 and pub.application_fee_minor==1000;assert reqs[0].code=='DIPLOME' and status=='upcoming'

def test_campaign_cannot_publish_without_requirements():
 a,i,p,y,cur=setup();c=campaign(a,i,p,y,cur)
 with pytest.raises(ValueError,match='requirements_required'):runtime.admissions_catalog.publish(a,i.id,c.id,1)

def test_campaign_rejects_unpublished_or_wrong_curriculum():
 a,i,p,y,cur=setup();draft=runtime.academic_catalog.create(a,i.id,program_unit_id=p.id,effective_academic_year_id=y.id,code='MED2',title='Médecine v2',version=2)
 n=datetime.now(UTC)
 with pytest.raises(ValueError,match='published_curriculum_required'):runtime.admissions_catalog.create(a,i.id,program_unit_id=p.id,academic_year_id=y.id,curriculum_id=draft.id,slug='bad',title='Bad',summary='',opens_at=n,closes_at=n+timedelta(days=1))

def test_campaign_validation_and_optimistic_lock():
 a,i,p,y,cur=setup();n=datetime.now(UTC)
 with pytest.raises(ValueError,match='invalid_dates'):runtime.admissions_catalog.create(a,i.id,program_unit_id=p.id,academic_year_id=y.id,curriculum_id=cur.id,slug='bad-date',title='Bad',summary='',opens_at=n,closes_at=n)
 c=campaign(a,i,p,y,cur);runtime.admissions_catalog.add_requirement(a,i.id,c.id,code='ID',label='Identité')
 with pytest.raises(ValueError,match='concurrent_modification'):runtime.admissions_catalog.publish(a,i.id,c.id,999)

def test_public_catalog_is_tenant_scoped_and_closed_campaign_disappears():
 a,i,p,y,cur=setup();c=campaign(a,i,p,y,cur);runtime.admissions_catalog.add_requirement(a,i.id,c.id,code='ID',label='Identité');pub=runtime.admissions_catalog.publish(a,i.id,c.id,1);b,j,_,_,_=setup()
 with pytest.raises(ValueError,match='public_campaign_not_found'):runtime.admissions_catalog.public_detail(j.slug,c.slug)
 runtime.admissions_catalog.close(a,i.id,c.id,pub.row_version)
 with pytest.raises(ValueError,match='public_campaign_not_found'):runtime.admissions_catalog.public_detail(i.slug,c.slug)
