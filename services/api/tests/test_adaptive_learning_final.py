from datetime import UTC,datetime,timedelta
from app.modules.adaptive_learning.application.service import AdaptiveLearningService
from app.modules.learning_experience.domain.model import *
N=datetime(2026,9,24,tzinfo=UTC)
class Plan: id='p';title='Anatomie';exam_at=N+timedelta(days=10);daily_minutes=45;course_ids=('bio','chim');state=ExamPlanState.ACTIVE
class L:
 def all_progress(self,a):return (LearningProgress(a,'bio','c',MasteryStage.PRACTICED,.9,2,1,6,10,N),)
 def unresolved_errors(self,a,limit):return (ErrorItem('e',a,'bio','c','quiz','q','p','a',2,False,N,N,N),)
 def all_review_cards(self,a,limit):return ()
 def recent_sessions(self,a,n):return ()
 def active_session(self,a):return None
 def exam_plans(self,a):return (Plan(),)
class R:
 def save(self,*x):self.saved=x
 def history(self,a,limit):return ({'readiness':55},)
def test_final_profile_has_gaps_exam_and_confidence():
 x=AdaptiveLearningService(L(),R(),lambda:N).profile('u'); assert x.model_version=='adaptive-v2'; assert x.gaps and x.gaps[0].severity>=20; assert x.exam_readiness and 'chim' in x.exam_readiness[0].at_risk_courses; assert any(d.action=='exam_focus' for d in x.decisions); assert x.confidence.value in {'low','medium','high'}
def test_history_delegates(): assert AdaptiveLearningService(L(),R(),lambda:N).history('u',10)[0]['readiness']==55
