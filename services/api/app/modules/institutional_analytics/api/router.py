from fastapi import APIRouter,Depends,HTTPException,Query
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.runtime import runtime
router=APIRouter()
def wrap(fn):
 try:return fn()
 except PermissionError as e:raise HTTPException(403,str(e)) from e
 except ValueError as e:raise HTTPException(422,str(e)) from e
@router.get('/institutions/{iid}/metrics')
def metrics(iid:str,auth:AuthContext=Depends(current_auth)):
 return [{'code':x.code,'version':x.version,'label':x.label,'description':x.description,'numerator':x.numerator,'denominator':x.denominator,'privacy_class':x.privacy_class} for x in wrap(lambda:runtime.institutional_analytics.definitions(auth.account_id,iid))]
@router.get('/institutions/{iid}/dashboard')
def dashboard(iid:str,academic_period_id:str|None=None,cohort_id:str|None=None,offering_id:str|None=None,auth:AuthContext=Depends(current_auth)):
 return wrap(lambda:runtime.institutional_analytics.dashboard(auth.account_id,iid,academic_period_id=academic_period_id,cohort_id=cohort_id,offering_id=offering_id))
@router.get('/institutions/{iid}/signals')
def signals(iid:str,academic_period_id:str|None=None,cohort_id:str|None=None,offering_id:str|None=None,auth:AuthContext=Depends(current_auth)):
 xs=wrap(lambda:runtime.institutional_analytics.signals(auth.account_id,iid,academic_period_id=academic_period_id,cohort_id=cohort_id,offering_id=offering_id));return [{'kind':x.kind.value,'severity':x.severity.value,'subject_type':x.subject_type,'subject_id':x.subject_id,'title':x.title,'explanation':x.explanation,'evidence':list(x.evidence)} for x in xs]
@router.get('/institutions/{iid}/units/{unit_id}/dashboard')
def unit_dashboard(iid:str,unit_id:str,academic_period_id:str|None=None,auth:AuthContext=Depends(current_auth)):
 return wrap(lambda:runtime.institutional_analytics.unit_dashboard(auth.account_id,iid,unit_id,academic_period_id=academic_period_id))
@router.post('/institutions/{iid}/snapshots')
def capture_snapshot(iid:str,academic_period_id:str|None=None,academic_unit_id:str|None=None,cohort_id:str|None=None,offering_id:str|None=None,auth:AuthContext=Depends(current_auth)):
 return wrap(lambda:runtime.institutional_analytics.capture_snapshot(auth.account_id,iid,academic_period_id=academic_period_id,academic_unit_id=academic_unit_id,cohort_id=cohort_id,offering_id=offering_id))
@router.get('/institutions/{iid}/snapshots')
def history(iid:str,scope_type:str,scope_id:str|None=None,academic_period_id:str|None=None,limit:int=50,auth:AuthContext=Depends(current_auth)):
 return {'items':list(wrap(lambda:runtime.institutional_analytics.history(auth.account_id,iid,scope_type=scope_type,scope_id=scope_id,academic_period_id=academic_period_id,limit=limit)))}
@router.get('/institutions/{iid}/comparisons')
def comparisons(iid:str,scope_type:str,scope_id:str|None=None,academic_period_id:str|None=None,auth:AuthContext=Depends(current_auth)):
 return wrap(lambda:runtime.institutional_analytics.compare_snapshots(auth.account_id,iid,scope_type=scope_type,scope_id=scope_id,academic_period_id=academic_period_id))
@router.get('/institutions/{iid}/export.csv')
def export_csv(iid:str,academic_period_id:str|None=None,academic_unit_id:str|None=None,cohort_id:str|None=None,offering_id:str|None=None,auth:AuthContext=Depends(current_auth)):
 from fastapi.responses import Response
 body=wrap(lambda:runtime.institutional_analytics.export_csv(auth.account_id,iid,academic_period_id=academic_period_id,academic_unit_id=academic_unit_id,cohort_id=cohort_id,offering_id=offering_id))
 return Response(body,media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="edunova-institutional-analytics.csv"'})

@router.get('/institutions/{iid}/pedagogical-intelligence')
def pedagogical_intelligence(iid:str,academic_period_id:str|None=None,cohort_id:str|None=None,offering_id:str|None=None,auth:AuthContext=Depends(current_auth)):
 return wrap(lambda:runtime.institutional_analytics.pedagogical_intelligence(auth.account_id,iid,academic_period_id=academic_period_id,cohort_id=cohort_id,offering_id=offering_id))
@router.get('/institutions/{iid}/executive-report')
def executive_report(iid:str,academic_period_id:str|None=None,academic_unit_id:str|None=None,cohort_id:str|None=None,offering_id:str|None=None,auth:AuthContext=Depends(current_auth)):
 return wrap(lambda:runtime.institutional_analytics.executive_report(auth.account_id,iid,academic_period_id=academic_period_id,academic_unit_id=academic_unit_id,cohort_id=cohort_id,offering_id=offering_id))

# Phase 15 — decision-support observatory; restricted to leadership and unit staff.
@router.get('/institutions/{iid}/intelligence/decision-brief')
def decision_brief(iid:str,academic_period_id:str|None=None,academic_unit_id:str|None=None,
                   cohort_id:str|None=None,offering_id:str|None=None,
                   auth:AuthContext=Depends(current_auth)):
 return wrap(lambda:runtime.institutional_analytics.decision_brief(auth.account_id,iid,
     academic_period_id=academic_period_id,academic_unit_id=academic_unit_id,
     cohort_id=cohort_id,offering_id=offering_id))

# Phase 15 — governance-only, privacy-controlled comparisons across periods.
@router.get('/institutions/{iid}/intelligence/period-comparison')
def period_comparison(iid:str,previous_period_id:str,current_period_id:str,
                      academic_unit_id:str|None=None,auth:AuthContext=Depends(current_auth)):
 return wrap(lambda:runtime.institutional_analytics.compare_period_briefs(auth.account_id,iid,
     previous_period_id=previous_period_id,current_period_id=current_period_id,
     academic_unit_id=academic_unit_id))

# Phase 15 — human-in-the-loop executive overview from governed data only.
@router.get('/institutions/{iid}/intelligence/executive-readout')
def executive_readout(iid:str,academic_period_id:str|None=None,academic_unit_id:str|None=None,
                      cohort_id:str|None=None,offering_id:str|None=None,
                      auth:AuthContext=Depends(current_auth)):
 return wrap(lambda:runtime.institutional_analytics.executive_readout(auth.account_id,iid,
     academic_period_id=academic_period_id,academic_unit_id=academic_unit_id,
     cohort_id=cohort_id,offering_id=offering_id))
