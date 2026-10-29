from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,Field
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
from app.modules.platform_governance.domain.model import PlatformRole
from app.runtime import runtime
router=APIRouter()
class GrantIn(BaseModel):role:PlatformRole;expected_version:int|None=Field(default=None,ge=1)
class DeactivateIn(BaseModel):expected_version:int=Field(ge=1)
def wrap(fn):
 try:return fn()
 except PermissionError as e:raise HTTPException(403,detail=str(e)) from e
 except ValueError as e:raise HTTPException(409 if 'concurrent' in str(e) else 422,detail=str(e)) from e
def out(x):return {'account_id':x.account_id,'role':x.role.value,'active':x.active,'row_version':x.row_version,'permissions':sorted(x.permissions),'granted_by':x.granted_by,'created_at':x.created_at,'updated_at':x.updated_at}
@router.get('/me')
def me(auth:AuthContext=Depends(current_auth)):
 x=runtime.platform_governance.membership(auth.account_id)
 if not x or not x.active:raise HTTPException(403,detail='platform_membership_required')
 return out(x)
@router.get('/dashboard')
def dashboard(auth:AuthContext=Depends(current_auth)):return wrap(lambda:runtime.platform_governance.dashboard(auth.account_id))
@router.get('/members')
def members(auth:AuthContext=Depends(current_auth)):
 wrap(lambda:runtime.platform_governance.require(auth.account_id,'platform.roles.manage'));return [out(x) for x in runtime.platform_governance_repo.list()]
@router.put('/members/{account_id}')
def grant(account_id:str,req:GrantIn,auth:AuthContext=Depends(current_auth)):return out(wrap(lambda:runtime.platform_governance.grant(auth.account_id,account_id,req.role,req.expected_version)))
@router.post('/members/{account_id}/deactivate')
def deactivate(account_id:str,req:DeactivateIn,auth:AuthContext=Depends(current_auth)):return out(wrap(lambda:runtime.platform_governance.deactivate(auth.account_id,account_id,req.expected_version)))


class InstitutionControlIn(BaseModel):
    state: str
    reason: str = Field(min_length=10,max_length=500)
    expected_version: int | None = Field(default=None,ge=1)

@router.get('/institutions/directory')
def institution_directory(
    limit:int=Query(default=50,ge=1,le=100),
    offset:int=Query(default=0,ge=0),
    state:str|None=Query(default=None),
    search:str|None=Query(default=None,max_length=120),
    auth:AuthContext=Depends(current_auth),
):
    wrap(lambda:runtime.platform_governance.require(auth.account_id,'platform.institutions.read'))
    if state is not None and state not in ('active','suspended','archived'):
        raise HTTPException(422,detail='invalid_institution_state')
    return runtime.platform_institution_controls.directory(limit=limit,offset=offset,state=state,search=search)

@router.get('/institutions/controls')
def institution_controls(auth:AuthContext=Depends(current_auth)):
    wrap(lambda:runtime.platform_governance.require(auth.account_id,'platform.institutions.read'))
    return runtime.platform_institution_controls.list()

@router.put('/institutions/{institution_id}/control')
def change_institution_control(institution_id:str, req:InstitutionControlIn, auth:AuthContext=Depends(current_auth)):
    from datetime import datetime, UTC
    wrap(lambda:runtime.platform_governance.require(auth.account_id,'platform.institutions.manage'))
    if not institution_id.strip() or len(institution_id)>64:raise HTTPException(422,detail='invalid_institution_id')
    if req.state not in ('active','suspended'):raise HTTPException(422,detail='invalid_institution_state')
    if not req.reason.strip():raise HTTPException(422,detail='reason_required')
    result=wrap(lambda:runtime.platform_institution_controls.change(
        institution_id,req.state,req.reason.strip(),auth.account_id,datetime.now(UTC),req.expected_version))
    runtime.audit.write(actor_id=auth.account_id,action='platform.institution.state_changed',
        entity_type='campus_institution',entity_id=institution_id,
        metadata={'state':req.state,'reason':req.reason.strip(),'version':result['row_version']})
    return result

@router.get('/institutions/statistics')
def institution_statistics(auth:AuthContext=Depends(current_auth)):
    wrap(lambda:runtime.platform_governance.require(auth.account_id,'platform.analytics.read'))
    return runtime.platform_institution_controls.statistics()

@router.get('/audit/events')
def platform_audit_events(limit:int=Query(default=25,ge=1,le=100),
                          offset:int=Query(default=0,ge=0),auth:AuthContext=Depends(current_auth)):
    wrap(lambda:runtime.platform_governance.require(auth.account_id,'platform.audit.read'))
    return runtime.audit.list_platform_events(limit=limit,offset=offset)


class InstitutionAssignmentIn(BaseModel):
    account_id: str = Field(min_length=1,max_length=64)
    role: str
    expected_version: int|None = Field(default=None,ge=1)
class AssignmentRevokeIn(BaseModel):
    expected_version: int = Field(ge=1)

@router.get('/institutions/{institution_id}/administrators')
def institution_administrators(institution_id:str,auth:AuthContext=Depends(current_auth)):
    wrap(lambda:runtime.platform_governance.require(auth.account_id,'platform.assignments.manage'))
    return wrap(lambda:runtime.platform_central_operations.assignments(institution_id))

@router.put('/institutions/{institution_id}/administrators')
def assign_institution_administrator(institution_id:str,req:InstitutionAssignmentIn,auth:AuthContext=Depends(current_auth)):
    wrap(lambda:runtime.platform_governance.require(auth.account_id,'platform.assignments.manage'))
    result=wrap(lambda:runtime.platform_central_operations.assign(institution_id,req.account_id,req.role,auth.account_id,req.expected_version))
    runtime.audit.write(actor_id=auth.account_id,action='platform.institution.administrator_assigned',entity_type='campus_institution',entity_id=institution_id,metadata={'role':req.role})
    return result

@router.post('/institutions/{institution_id}/administrators/{account_id}/revoke')
def revoke_institution_administrator(institution_id:str,account_id:str,req:AssignmentRevokeIn,auth:AuthContext=Depends(current_auth)):
    wrap(lambda:runtime.platform_governance.require(auth.account_id,'platform.assignments.manage'))
    result=wrap(lambda:runtime.platform_central_operations.revoke(institution_id,account_id,auth.account_id,req.expected_version))
    runtime.audit.write(actor_id=auth.account_id,action='platform.institution.administrator_revoked',entity_type='campus_institution',entity_id=institution_id,metadata={})
    return result

class SupportTicketIn(BaseModel):
    institution_id: str = Field(min_length=1,max_length=64)
    title: str = Field(min_length=5,max_length=160)
    description: str = Field(min_length=10,max_length=1500)
    priority: str = 'normal'
class SupportTicketUpdateIn(BaseModel):
    state: str
    assigned_to: str|None = Field(default=None,max_length=64)
    expected_version: int = Field(ge=1)

@router.get('/support/tickets')
def support_tickets(limit:int=Query(default=25,ge=1,le=100),offset:int=Query(default=0,ge=0),state:str|None=None,institution_id:str|None=None,auth:AuthContext=Depends(current_auth)):
    wrap(lambda:runtime.platform_governance.require(auth.account_id,'platform.support.read'))
    if state and state not in ('open','in_progress','resolved','closed'):raise HTTPException(422,detail='invalid_ticket_state')
    return runtime.platform_central_operations.tickets(limit,offset,state,institution_id)

@router.post('/support/tickets',status_code=201)
def create_support_ticket(req:SupportTicketIn,auth:AuthContext=Depends(current_auth)):
    wrap(lambda:runtime.platform_governance.require(auth.account_id,'platform.support.manage'))
    result=wrap(lambda:runtime.platform_central_operations.create_ticket(req.institution_id,req.title,req.description,req.priority,auth.account_id))
    runtime.audit.write(actor_id=auth.account_id,action='platform.support.ticket_created',entity_type='platform_support_ticket',entity_id=result['id'],metadata={})
    return result

@router.put('/support/tickets/{ticket_id}')
def update_support_ticket(ticket_id:str,req:SupportTicketUpdateIn,auth:AuthContext=Depends(current_auth)):
    wrap(lambda:runtime.platform_governance.require(auth.account_id,'platform.support.manage'))
    result=wrap(lambda:runtime.platform_central_operations.update_ticket(ticket_id,req.state,req.assigned_to,auth.account_id,req.expected_version))
    runtime.audit.write(actor_id=auth.account_id,action='platform.support.ticket_updated',entity_type='platform_support_ticket',entity_id=ticket_id,metadata={'state':req.state})
    return result
