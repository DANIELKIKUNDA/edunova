from fastapi import APIRouter,Depends,HTTPException,Response
from pydantic import BaseModel
from app.runtime import runtime
from app.modules.identity.api.router import current_auth
from app.modules.identity.application.auth_context import AuthContext
router=APIRouter()
def call(f):
 try:return f()
 except PermissionError as e:raise HTTPException(403,str(e))
 except ValueError as e:raise HTTPException(400,str(e))
class IssueIn(BaseModel):title:str;replaces_document_id:str|None=None
class RevokeIn(BaseModel):reason:str
@router.post('/institutions/{iid}/requests/{rid}/issue')
def issue(iid:str,rid:str,q:IssueIn,auth:AuthContext=Depends(current_auth)):
 doc,token=call(lambda:runtime.official_documents.issue(auth.account_id,iid,rid,q.title,q.replaces_document_id))
 return {'id':doc.id,'serial_number':doc.serial_number,'sha256':doc.sha256_hex,'verification_token':token,'status':doc.state.value}
@router.get('/institutions/{iid}/documents/{did}/pdf')
def pdf(iid:str,did:str,auth:AuthContext=Depends(current_auth)):
 doc=call(lambda:runtime.official_documents.get(auth.account_id,iid,did))
 return Response(doc.pdf_bytes,media_type='application/pdf',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})
@router.post('/institutions/{iid}/documents/{did}/revoke')
def revoke(iid:str,did:str,q:RevokeIn,auth:AuthContext=Depends(current_auth)):
 call(lambda:runtime.official_documents.revoke(auth.account_id,iid,did,q.reason));return {'status':'revoked'}
@router.get('/verify/{token}')
def verify(token:str):return runtime.official_documents.verify(token)

@router.get('/institutions/{iid}/documents/{did}/history')
def history(iid:str,did:str,auth:AuthContext=Depends(current_auth)):
 events=call(lambda:runtime.official_documents.history(auth.account_id,iid,did))
 return [{'id':e.id,'event_type':e.event_type,'actor_id':e.actor_id,'reason':e.reason,'created_at':e.created_at.isoformat()} for e in events]

class TemplateIn(BaseModel):kind:str;version:str;name:str
@router.post('/institutions/{iid}/templates')
def create_template(iid:str,q:TemplateIn,auth:AuthContext=Depends(current_auth)):
 t=call(lambda:runtime.official_documents.create_template(auth.account_id,iid,q.kind,q.version,q.name));return {'id':t.id,'kind':t.kind,'version':t.version,'state':t.state.value}
@router.post('/institutions/{iid}/templates/{tid}/publish')
def publish_template(iid:str,tid:str,auth:AuthContext=Depends(current_auth)):
 call(lambda:runtime.official_documents.publish_template(auth.account_id,iid,tid));return {'status':'published'}
