from __future__ import annotations
from dataclasses import replace
from uuid import uuid4
from app.modules.tutor.domain.model import *

class TutorService:
    def __init__(self,repo,now): self.repo=repo; self.now=now
    def start(self,account_id,course_id=None,target_concept_id=None,subject_domain='general',high_stakes=False):
        x=TutorSession(uuid4().hex,account_id,course_id,target_concept_id,subject_domain,high_stakes,TutorSessionState.ACTIVE,0,0,1,self.now(),self.now()); self.repo.save_session(x); return x
    def decide(self,session,question,evidence=(),prerequisites=(),source_count=0,wants_answer=False,mutation_id=None):
        if session.state!=TutorSessionState.ACTIVE: raise ValueError('tutor_session_not_active')
        if mutation_id:
            old=self.repo.turn_by_mutation(session.account_id,mutation_id)
            if old:return old
        q=question.strip()
        if len(q)<2:raise ValueError('question_too_short')
        ev=tuple(evidence); weak=sorted((e for e in ev if e.mastery<0.7 or e.error_count>=2),key=lambda e:(e.mastery,-e.error_count))
        missing=next((p for p in prerequisites if any(e.concept_id==p and (e.mastery<0.7 or e.error_count>=2) for e in ev)),None)
        requires_sources=session.high_stakes or session.course_id is not None
        if session.high_stakes and source_count<1:
            d=TutorDecision(TutorMove.ABSTAIN,'high_stakes_requires_validated_source',session.target_concept_id,'understand',session.hint_level,True,'attach_validated_source')
        elif missing:
            d=TutorDecision(TutorMove.PREREQUISITE,'published_prerequisite_is_weak',missing,'understand',session.hint_level,requires_sources,'repair_prerequisite_then_return')
        elif weak and weak[0].error_count>=2:
            d=TutorDecision(TutorMove.REMEDIATE,'repeated_errors_require_targeted_remediation',weak[0].concept_id,weak[0].bloom_level,session.hint_level,requires_sources,'open_targeted_remediation')
        elif wants_answer:
            d=TutorDecision(TutorMove.EXPLAIN,'explicit_explanation_request',session.target_concept_id,'understand',session.hint_level,requires_sources,'explain_then_check_understanding')
        elif session.hint_level<2 and session.turn_count>0:
            d=TutorDecision(TutorMove.HINT,'progressive_hint_before_solution',session.target_concept_id,'apply',session.hint_level+1,requires_sources,'ask_student_to_retry')
        else:
            d=TutorDecision(TutorMove.SOCRATIC,'elicit_reasoning_before_direct_solution',session.target_concept_id,'analyze',session.hint_level,requires_sources,'ask_one_diagnostic_question')
        t=TutorTurn(uuid4().hex,session.id,session.account_id,q,d,tuple(f'{e.concept_id}:{e.mastery:.2f}:{e.error_count}' for e in ev),self.now(),mutation_id); self.repo.save_turn(t)
        updated=replace(session,hint_level=d.hint_level,turn_count=session.turn_count+1,row_version=session.row_version+1,updated_at=self.now());self.repo.save_session(updated);return t
    def close(self,account_id,session_id,expected_version):
        x=self.repo.session(account_id,session_id)
        if not x:raise ValueError('tutor_session_not_found')
        if x.row_version!=expected_version:raise ValueError('tutor_version_conflict')
        y=replace(x,state=TutorSessionState.CLOSED,row_version=x.row_version+1,updated_at=self.now());self.repo.save_session(y);return y
