from datetime import UTC, datetime, timedelta
import pytest
from app.modules.pilot_readiness.application.service import PilotReadinessService

def test_checklist_blocks_until_complete():
 s=PilotReadinessService(); assert not s.checklist(institution_configured=True,academic_structure=True,staff_ready=True,students_ready=False)['ready']; assert s.checklist(institution_configured=True,academic_structure=True,staff_ready=True,students_ready=True)['ready']
def test_invitation_is_one_time():
 s=PilotReadinessService(); t=s.create_invitation('u1','TEACHER'); assert s.consume_invitation(t).institution_id=='u1';
 with pytest.raises(ValueError): s.consume_invitation(t)
def test_invitation_expires():
 now=[datetime(2026,1,1,tzinfo=UTC)]; s=PilotReadinessService(lambda:now[0]); t=s.create_invitation('u1','STUDENT',1); now[0]+=timedelta(hours=2)
 with pytest.raises(ValueError): s.consume_invitation(t)
def test_growth_event_strips_sensitive_metadata():
 s=PilotReadinessService(); e=s.track('activated','a',{'course':'math','email':'x@y.z','document_text':'secret'}); assert e['metadata']=={'course':'math'}
def test_diagnostic_has_no_private_payload():
 d=PilotReadinessService().diagnostic('0.32.0','r1'); assert d['request_id']=='r1' and 'document' not in d
