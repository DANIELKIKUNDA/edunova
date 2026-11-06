from datetime import UTC,datetime,timedelta
from app.modules.adaptive_learning.application.service import AdaptiveLearningService
from app.modules.learning_experience.domain.model import *
N=datetime(2026,9,24,tzinfo=UTC)
class L:
 def all_progress(self,a):return (LearningProgress(a,'bio','c',MasteryStage.STUDIED,.8,0,0,6,10,N),)
 def unresolved_errors(self,a,limit):return (ErrorItem('e',a,'bio','c','quiz','q','p','a',1,False,N,N,N),)
 def all_review_cards(self,a,limit):return ()
 def recent_sessions(self,a,n):return ()
 def active_session(self,a):return None
class R:
 def save(self,*x):pass
def test_explainable_priority():
 x=AdaptiveLearningService(L(),R(),lambda:N).profile('u');assert x.decisions[0].action=='error_repair';assert x.risk.value=='watch';assert x.evidence_count==1
