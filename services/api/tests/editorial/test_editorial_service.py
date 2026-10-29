from datetime import UTC, datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.shared.infrastructure.database import Base
from app.modules.editorial.application.service import EditorialService
from app.modules.editorial.infrastructure.sqlalchemy_repo import SqlAlchemyEditorialRepository
from app.modules.editorial.domain.model import EditorialMember, EditorialRole, ContentKind, RiskLevel, RightsStatus, EditorialState

@pytest.fixture
def env(tmp_path):
    e=create_engine(f"sqlite+pysqlite:///{tmp_path/'e.db'}",connect_args={'check_same_thread':False}); Base.metadata.create_all(e); sf=sessionmaker(bind=e,expire_on_commit=False)
    repo=SqlAlchemyEditorialRepository(sf); svc=EditorialService(repo,now=lambda:datetime(2026,9,22,12,0,tzinfo=UTC))
    for aid,role in [('owner',EditorialRole.OWNER),('editor',EditorialRole.EDITOR),('reviewer',EditorialRole.REVIEWER),('publisher',EditorialRole.PUBLISHER)]: repo.save_member(EditorialMember(aid,role))
    return svc,repo

def make_item(svc):
    return svc.create_item(actor_id='editor',kind=ContentKind.COURSE,title='Physiologie',faculty_domain='Médecine',program='Médecine humaine',level='BAC1',semester='S1',risk=RiskLevel.MEDICAL,rights_status=RightsStatus.AUTHORIZED,source_fingerprint='abc')

def test_medical_content_requires_four_eyes(env):
    svc,repo=env; item=make_item(svc); svc.add_revision(actor_id='editor',item_id=item.id,payload={'summary':'x'},source_fingerprint='abc',ai_generated=True,prompt_version='p1'); svc.submit_review(actor_id='editor',item_id=item.id)
    # editor is not reviewer anyway; high-risk self-review is also blocked if roles later converge
    with pytest.raises(PermissionError): svc.review(actor_id='editor',item_id=item.id,approve=True)
    reviewed=svc.review(actor_id='reviewer',item_id=item.id,approve=True,checklist={'factual_accuracy':True,'source_traceability':True,'scope_alignment':True,'language_quality':True,'safety':True})
    assert reviewed.state==EditorialState.APPROVED

def test_unknown_rights_block_review(env):
    svc,repo=env
    item=svc.create_item(actor_id='editor',kind=ContentKind.ASSESSMENT,title='Ancienne interrogation',faculty_domain='Médecine',program='Médecine',level='BAC1',semester=None,risk=RiskLevel.STANDARD,rights_status=RightsStatus.UNKNOWN)
    svc.add_revision(actor_id='editor',item_id=item.id,payload={'questions':[1]},source_fingerprint='q')
    with pytest.raises(ValueError,match='distribution_rights_not_cleared'): svc.submit_review(actor_id='editor',item_id=item.id)

def test_publish_only_approved_and_immutable(env):
    svc,repo=env; item=make_item(svc); rev=svc.add_revision(actor_id='editor',item_id=item.id,payload={'chapter':'A'},source_fingerprint='abc'); svc.submit_review(actor_id='editor',item_id=item.id); svc.review(actor_id='reviewer',item_id=item.id,approve=True,checklist={'factual_accuracy':True,'source_traceability':True,'scope_alignment':True,'language_quality':True,'safety':True}); pub=svc.publish(actor_id='publisher',item_id=item.id,changelog='Initial')
    assert pub.state==EditorialState.PUBLISHED and pub.published_revision_id==rev.id
    rev2=svc.add_revision(actor_id='editor',item_id=item.id,payload={'chapter':'B'},source_fingerprint='def')
    latest=repo.get_item(item.id); assert rev2.revision_no==2 and latest.state==EditorialState.DRAFT and latest.published_revision_id==rev.id

def test_changes_requested_returns_to_editor(env):
    svc,repo=env; item=make_item(svc); svc.add_revision(actor_id='editor',item_id=item.id,payload={'x':1},source_fingerprint='a'); svc.submit_review(actor_id='editor',item_id=item.id); changed=svc.review(actor_id='reviewer',item_id=item.id,approve=False,comment='Source à corriger')
    assert changed.state==EditorialState.CHANGES_REQUESTED
    rev2=svc.add_revision(actor_id='editor',item_id=item.id,payload={'x':2},source_fingerprint='b',note='corrigé')
    assert rev2.revision_no==2 and repo.get_item(item.id).state==EditorialState.DRAFT

def test_internal_only_cannot_be_published(env):
    svc,repo=env
    item=svc.create_item(actor_id='editor',kind=ContentKind.OTHER,title='Note interne',faculty_domain='Médecine',program='Médecine',level='BAC1',semester=None,risk=RiskLevel.STANDARD,rights_status=RightsStatus.INTERNAL_ONLY)
    svc.add_revision(actor_id='editor',item_id=item.id,payload={'x':1},source_fingerprint='x'); svc.submit_review(actor_id='editor',item_id=item.id); svc.review(actor_id='reviewer',item_id=item.id,approve=True,checklist={'source_traceability':True,'structure_quality':True,'rights_checked':True})
    with pytest.raises(ValueError,match='internal_only'): svc.publish(actor_id='publisher',item_id=item.id)

def test_dashboard_counts_workflow(env):
    svc,repo=env; item=make_item(svc); svc.add_revision(actor_id='editor',item_id=item.id,payload={'x':1},source_fingerprint='x'); svc.submit_review(actor_id='editor',item_id=item.id)
    d=svc.dashboard('reviewer'); assert d['needs_review']==1 and d['total']==1


def test_high_risk_ai_requires_prompt_version(env):
    svc,repo=env; item=make_item(svc); svc.add_revision(actor_id='editor',item_id=item.id,payload={'x':1},source_fingerprint='src',ai_generated=True,prompt_version=None)
    with pytest.raises(ValueError,match='ai_prompt_version_required'): svc.submit_review(actor_id='editor',item_id=item.id)

def test_owner_manages_internal_roles(env):
    svc,repo=env; m=svc.set_member(actor_id='owner',account_id='new-reviewer',role=EditorialRole.REVIEWER,active=True)
    assert m.role==EditorialRole.REVIEWER and any(x.account_id=='new-reviewer' for x in svc.members('owner'))
    with pytest.raises(PermissionError): svc.members('editor')

def test_ocr_source_must_be_human_verified_before_review(env):
    svc,repo=env; item=make_item(svc)
    src=svc.add_source(actor_id='editor',item_id=item.id,filename='scan.jpg',checksum_sha256='a'*64,mime_type='image/jpeg',ocr_confidence=0.82)
    svc.add_revision(actor_id='editor',item_id=item.id,payload={'x':1},source_fingerprint='src',ai_generated=False)
    with pytest.raises(ValueError,match='ocr_source_requires_human_verification'): svc.submit_review(actor_id='editor',item_id=item.id)
    svc.verify_source(actor_id='reviewer',source_id=src.id)
    assert svc.submit_review(actor_id='editor',item_id=item.id).state==EditorialState.IN_REVIEW

def test_duplicate_source_checksum_is_blocked_across_items(env):
    svc,repo=env; i1=make_item(svc)
    svc.add_source(actor_id='editor',item_id=i1.id,filename='a.jpg',checksum_sha256='b'*64,ocr_confidence=.9)
    i2=svc.create_item(actor_id='editor',kind=ContentKind.ASSESSMENT,title='Interro 2',faculty_domain='Médecine',program='Médecine',level='BAC1',semester='S1',risk=RiskLevel.STANDARD,rights_status=RightsStatus.AUTHORIZED)
    with pytest.raises(ValueError,match='duplicate_source_checksum'): svc.add_source(actor_id='editor',item_id=i2.id,filename='copy.jpg',checksum_sha256='b'*64,ocr_confidence=.9)

def _medical_checklist():
    return {'factual_accuracy':True,'source_traceability':True,'scope_alignment':True,'language_quality':True,'safety':True}

def _standard_checklist():
    return {'source_traceability':True,'structure_quality':True,'rights_checked':True}

def test_review_checklist_is_required_for_approval(env):
    svc,repo=env; item=make_item(svc); svc.add_revision(actor_id='editor',item_id=item.id,payload={'x':1},source_fingerprint='src'); svc.submit_review(actor_id='editor',item_id=item.id)
    with pytest.raises(ValueError,match='review_checklist_incomplete'): svc.review(actor_id='reviewer',item_id=item.id,approve=True)
    approved=svc.review(actor_id='reviewer',item_id=item.id,approve=True,checklist=_medical_checklist())
    assert approved.state==EditorialState.APPROVED

def test_optimistic_concurrency_blocks_stale_writer(env):
    svc,repo=env; item=make_item(svc)
    assert item.row_version==1
    svc.add_revision(actor_id='editor',item_id=item.id,payload={'x':1},source_fingerprint='src',expected_version=1)
    with pytest.raises(ValueError,match='editorial_concurrent_modification'):
        svc.submit_review(actor_id='editor',item_id=item.id,expected_version=1)

def test_assignments_enforce_role_and_assignee(env):
    svc,repo=env; item=make_item(svc); svc.add_revision(actor_id='editor',item_id=item.id,payload={'x':1},source_fingerprint='src'); svc.submit_review(actor_id='editor',item_id=item.id)
    from app.modules.editorial.domain.model import AssignmentStage
    with pytest.raises(ValueError,match='assignee_role_mismatch'):
        svc.assign(actor_id='owner',item_id=item.id,assignee_id='editor',stage=AssignmentStage.REVIEW)
    svc.assign(actor_id='owner',item_id=item.id,assignee_id='reviewer',stage=AssignmentStage.REVIEW)
    with pytest.raises(PermissionError,match='review_assigned_to_another_member'):
        svc.review(actor_id='owner',item_id=item.id,approve=True,checklist=_medical_checklist())
    assert svc.review(actor_id='reviewer',item_id=item.id,approve=True,checklist=_medical_checklist()).state==EditorialState.APPROVED

def test_high_risk_reviewer_cannot_also_publish(env):
    svc,repo=env; item=make_item(svc); svc.add_revision(actor_id='editor',item_id=item.id,payload={'x':1},source_fingerprint='src'); svc.submit_review(actor_id='editor',item_id=item.id)
    svc.review(actor_id='owner',item_id=item.id,approve=True,checklist=_medical_checklist())
    with pytest.raises(ValueError,match='high_risk_separation_of_duties_required'):
        svc.publish(actor_id='owner',item_id=item.id,changelog='Initial')

def test_restore_revision_creates_new_draft(env):
    svc,repo=env; item=make_item(svc); r1=svc.add_revision(actor_id='editor',item_id=item.id,payload={'chapter':'A'},source_fingerprint='a'); r2=svc.add_revision(actor_id='editor',item_id=item.id,payload={'chapter':'B'},source_fingerprint='b')
    restored=svc.restore_revision(actor_id='editor',item_id=item.id,revision_id=r1.id,note='Retour à A')
    assert restored.revision_no==3 and 'Retour à A'==restored.note
    assert repo.get_item(item.id).state==EditorialState.DRAFT

def test_search_filters_and_pagination(env):
    svc,repo=env; make_item(svc)
    svc.create_item(actor_id='editor',kind=ContentKind.ASSESSMENT,title='Interrogation Chimie',faculty_domain='Sciences',program='Chimie',level='L1',semester='S1',risk=RiskLevel.STANDARD,rights_status=RightsStatus.AUTHORIZED)
    rows,total=svc.search('reviewer',query='chimie',kind=ContentKind.ASSESSMENT,limit=10,offset=0)
    assert total==1 and rows[0].title=='Interrogation Chimie'

def test_source_ocr_importer_cannot_self_verify_without_owner(env):
    svc,repo=env; item=make_item(svc); src=svc.add_source(actor_id='editor',item_id=item.id,filename='scan.jpg',checksum_sha256='c'*64,ocr_confidence=.91)
    with pytest.raises(ValueError,match='source_verification_requires_second_person'):
        svc.verify_source(actor_id='editor',source_id=src.id)
    assert svc.verify_source(actor_id='reviewer',source_id=src.id).human_verified
