from __future__ import annotations
import hashlib, secrets
from datetime import UTC, datetime, timedelta
from app.modules.pilot_readiness.domain.model import PilotCheck, PilotInvitation

class PilotReadinessService:
    def __init__(self, now=lambda: datetime.now(UTC)):
        self.now=now; self._invites={}; self._events=[]
    def checklist(self, *, institution_configured: bool, academic_structure: bool, staff_ready: bool, students_ready: bool):
        checks=[PilotCheck('institution','Institution configurée',institution_configured),PilotCheck('structure','Structure académique configurée',academic_structure),PilotCheck('staff','Équipe Campus prête',staff_ready),PilotCheck('students','Étudiants importés/invités',students_ready)]
        return {'ready':all(c.ready for c in checks if c.blocking),'checks':[c.__dict__ if hasattr(c,'__dict__') else {'code':c.code,'label':c.label,'ready':c.ready,'blocking':c.blocking} for c in checks]}
    def create_invitation(self,institution_id:str,role:str,ttl_hours:int=72):
        raw=secrets.token_urlsafe(32); digest=hashlib.sha256(raw.encode()).hexdigest()
        inv=PilotInvitation(digest,institution_id,role,self.now()+timedelta(hours=max(1,min(ttl_hours,168))))
        self._invites[digest]=inv; return raw
    def consume_invitation(self,raw:str):
        digest=hashlib.sha256(raw.encode()).hexdigest(); inv=self._invites.get(digest)
        if not inv or inv.used or inv.expires_at<=self.now(): raise ValueError('invalid_or_expired_invitation')
        used=PilotInvitation(inv.token,inv.institution_id,inv.role,inv.expires_at,True); self._invites[digest]=used; return used
    def track(self,name:str,actor_id:str|None=None,metadata:dict|None=None):
        safe={k:v for k,v in (metadata or {}).items() if k not in {'email','phone','document_text','message'}}
        event={'name':name,'actor_id':actor_id,'metadata':safe,'at':self.now().isoformat()}; self._events.append(event); return event
    def diagnostic(self,version:str,request_id:str|None=None):
        return {'product':'EduNova','version':version,'request_id':request_id,'generated_at':self.now().isoformat(),'privacy':'No private document/chat content included.'}
