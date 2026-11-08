from fastapi import APIRouter,Depends,Query
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.runtime import runtime
router=APIRouter()
@router.get('/profile')
def profile(auth:AuthContext=Depends(current_auth)):
 x=runtime.adaptive_learning.profile(auth.account_id)
 return {'mastery_score':x.mastery,'readiness_score':x.readiness,'consistency_score':x.consistency,'risk_band':x.risk.value,'confidence_band':x.confidence.value,'evidence_count':x.evidence_count,'model_version':x.model_version,'recommendations':[d.__dict__ for d in x.decisions],'knowledge_gaps':[g.__dict__ for g in x.gaps],'exam_readiness':[e.__dict__ for e in x.exam_readiness],'disclaimer':'Recommandations explicables fondées sur les preuves EduNova; elles ne constituent pas une certitude sur la maîtrise.'}
@router.get('/history')
def history(limit:int=Query(30,ge=1,le=90),auth:AuthContext=Depends(current_auth)):
 return {'items':runtime.adaptive_learning.history(auth.account_id,limit),'limit':limit}
