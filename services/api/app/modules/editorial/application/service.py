from __future__ import annotations
import json
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4
from app.modules.editorial.domain.model import *

def _now(): return datetime.now(UTC)

class EditorialService:
    HIGH_RISK_CHECKS=('factual_accuracy','source_traceability','scope_alignment','language_quality','safety')
    STANDARD_CHECKS=('source_traceability','structure_quality','rights_checked')
    def __init__(self, repo, audit=None, projector=None, now=_now): self.repo=repo; self.audit=audit; self.projector=projector; self.now=now
    def _member(self, actor_id:str)->EditorialMember:
        m=self.repo.get_member(actor_id)
        if not m or not m.active: raise PermissionError('editorial_access_denied')
        return m
    def _require(self, actor_id:str, *roles:EditorialRole):
        m=self._member(actor_id)
        if m.role not in roles and m.role != EditorialRole.OWNER: raise PermissionError('editorial_role_denied')
        return m
    def _save_transition(self, before:EditorialItem, after:EditorialItem)->EditorialItem:
        out=replace(after,row_version=before.row_version+1)
        self.repo.save_item(out,expected_version=before.row_version)
        return out
    def _assert_expected(self,item:EditorialItem,expected_version:int|None):
        if expected_version is not None and item.row_version!=int(expected_version): raise ValueError('editorial_concurrent_modification')
    def create_item(self, *, actor_id:str, kind:ContentKind, title:str, faculty_domain:str, program:str, level:str, semester:str|None, risk:RiskLevel, rights_status:RightsStatus, rights_note:str='', source_fingerprint:str=''):
        self._require(actor_id, EditorialRole.EDITOR)
        t=self.now(); item=EditorialItem(str(uuid4()),kind,title.strip(),faculty_domain.strip(),program.strip(),level.strip(),semester,EditorialState.DRAFT,risk,rights_status,rights_note,source_fingerprint,actor_id,t,t,row_version=1)
        if not item.title: raise ValueError('title_required')
        self.repo.save_item(item); self._audit(actor_id,'editorial.item.created',item.id,{'kind':kind.value,'risk':risk.value}); return item

    def update_item(self, *, actor_id:str,item_id:str,title:str|None=None,faculty_domain:str|None=None,program:str|None=None,level:str|None=None,semester:str|None=None,risk:RiskLevel|None=None,rights_status:RightsStatus|None=None,rights_note:str|None=None,expected_version:int|None=None):
        self._require(actor_id,EditorialRole.EDITOR); item=self._item(item_id); self._assert_expected(item,expected_version)
        if item.state in {EditorialState.IN_REVIEW,EditorialState.APPROVED,EditorialState.ARCHIVED}: raise ValueError('item_metadata_locked_in_current_state')
        if item.state==EditorialState.PUBLISHED: raise ValueError('published_item_requires_new_revision')
        next_item=replace(item,
            title=item.title if title is None else title.strip(),
            faculty_domain=item.faculty_domain if faculty_domain is None else faculty_domain.strip(),
            program=item.program if program is None else program.strip(),
            level=item.level if level is None else level.strip(),
            semester=item.semester if semester is None else semester,
            risk=item.risk if risk is None else risk,
            rights_status=item.rights_status if rights_status is None else rights_status,
            rights_note=item.rights_note if rights_note is None else rights_note,
            updated_at=self.now(),
        )
        if not next_item.title: raise ValueError('title_required')
        out=self._save_transition(item,next_item); self._audit(actor_id,'editorial.item.updated',item.id,{'row_version':out.row_version}); return out

    def add_revision(self, *, actor_id:str, item_id:str, payload:dict, source_fingerprint:str, ai_generated:bool=False, prompt_version:str|None=None, note:str='', expected_version:int|None=None):
        self._require(actor_id, EditorialRole.EDITOR)
        item=self._item(item_id); self._assert_expected(item,expected_version)
        if item.state == EditorialState.ARCHIVED: raise ValueError('archived_item_is_immutable')
        revs=self.repo.list_revisions(item_id); n=(max((r.revision_no for r in revs),default=0)+1); t=self.now()
        rev=EditorialRevision(str(uuid4()),item_id,n,json.dumps(payload,ensure_ascii=False,sort_keys=True),source_fingerprint,ai_generated,prompt_version,actor_id,t,note)
        self.repo.save_revision(rev)
        self._save_transition(item,replace(item,current_revision_id=rev.id,state=EditorialState.DRAFT,updated_at=t))
        self._audit(actor_id,'editorial.revision.created',item_id,{'revision_id':rev.id,'revision_no':n,'ai_generated':ai_generated}); return rev
    def restore_revision(self, *, actor_id:str,item_id:str,revision_id:str,note:str='',expected_version:int|None=None):
        self._require(actor_id,EditorialRole.EDITOR); item=self._item(item_id); self._assert_expected(item,expected_version)
        rev=self.repo.get_revision(revision_id)
        if not rev or rev.item_id!=item_id: raise ValueError('revision_not_found')
        payload=json.loads(rev.payload_json or '{}')
        return self.add_revision(actor_id=actor_id,item_id=item_id,payload=payload,source_fingerprint=rev.source_fingerprint,ai_generated=rev.ai_generated,prompt_version=rev.prompt_version,note=note or f'Restauration de R{rev.revision_no}',expected_version=item.row_version)
    def submit_review(self, *, actor_id:str, item_id:str, expected_version:int|None=None):
        self._require(actor_id, EditorialRole.EDITOR); item=self._item(item_id); self._assert_expected(item,expected_version)
        gates=self.quality_gates(actor_id,item_id,phase='review')
        failed=[g for g in gates if not g.passed]
        if failed: raise ValueError(failed[0].code)
        out=self._save_transition(item,replace(item,state=EditorialState.IN_REVIEW,updated_at=self.now()))
        self._audit(actor_id,'editorial.review.submitted',item.id); return out
    def review(self, *, actor_id:str, item_id:str, approve:bool, comment:str='', checklist:dict|None=None, quality_score:int|None=None, expected_version:int|None=None):
        self._require(actor_id, EditorialRole.REVIEWER); item=self._item(item_id); self._assert_expected(item,expected_version)
        if item.state != EditorialState.IN_REVIEW or not item.current_revision_id: raise ValueError('item_not_in_review')
        rev=self.repo.get_revision(item.current_revision_id)
        assignment=self.repo.get_active_assignment(item.id,AssignmentStage.REVIEW)
        if assignment and assignment.assignee_id!=actor_id: raise PermissionError('review_assigned_to_another_member')
        if item.risk in {RiskLevel.MEDICAL,RiskLevel.HIGH_STAKES} and rev.created_by==actor_id: raise ValueError('four_eyes_required')
        for src in self.repo.list_sources(item.id):
            if src.ocr_confidence is not None and not src.human_verified: raise ValueError('ocr_source_requires_human_verification')
        checklist={str(k):bool(v) for k,v in (checklist or {}).items()}
        if approve:
            required=self.HIGH_RISK_CHECKS if item.risk in {RiskLevel.MEDICAL,RiskLevel.HIGH_STAKES} else self.STANDARD_CHECKS
            missing=[k for k in required if checklist.get(k) is not True]
            if missing: raise ValueError('review_checklist_incomplete')
        elif not comment.strip(): raise ValueError('review_comment_required')
        if quality_score is None and checklist:
            quality_score=round(100*sum(1 for v in checklist.values() if v)/max(1,len(checklist)))
        if quality_score is not None and not 0<=int(quality_score)<=100: raise ValueError('quality_score_out_of_range')
        decision='approved' if approve else 'changes_requested'
        review=ReviewDecision(str(uuid4()),item.id,rev.id,actor_id,decision,comment.strip(),self.now(),json.dumps(checklist,sort_keys=True),quality_score)
        self.repo.save_review(review)
        self.repo.complete_assignment(item.id,AssignmentStage.REVIEW)
        out=self._save_transition(item,replace(item,state=EditorialState.APPROVED if approve else EditorialState.CHANGES_REQUESTED,updated_at=self.now()))
        self._audit(actor_id,f'editorial.review.{decision}',item.id,{'revision_id':rev.id,'quality_score':quality_score}); return out
    def publish(self, *, actor_id:str, item_id:str, changelog:str='', expected_version:int|None=None):
        self._require(actor_id, EditorialRole.PUBLISHER); item=self._item(item_id); self._assert_expected(item,expected_version)
        if item.state != EditorialState.APPROVED or not item.current_revision_id: raise ValueError('approved_revision_required')
        if item.rights_status not in {RightsStatus.AUTHORIZED,RightsStatus.PUBLIC_DOMAIN, RightsStatus.INTERNAL_ONLY}: raise ValueError('distribution_rights_not_cleared')
        if item.rights_status==RightsStatus.INTERNAL_ONLY: raise ValueError('internal_only_cannot_publish')
        if not changelog.strip(): raise ValueError('publication_changelog_required')
        assignment=self.repo.get_active_assignment(item.id,AssignmentStage.PUBLICATION)
        if assignment and assignment.assignee_id!=actor_id: raise PermissionError('publication_assigned_to_another_member')
        revision=self.repo.get_revision(item.current_revision_id)
        if item.risk in {RiskLevel.MEDICAL,RiskLevel.HIGH_STAKES}:
            approved=[r for r in self.repo.list_reviews(item.id) if r.revision_id==revision.id and r.decision=='approved']
            if not approved: raise ValueError('approved_review_required')
            reviewer=approved[-1].reviewer_id
            if actor_id in {reviewer,revision.created_by}: raise ValueError('high_risk_separation_of_duties_required')
        t=self.now()
        if self.projector is not None:self.projector.project(item=item, revision=revision, changelog=changelog.strip(), published_at=t)
        rec=PublicationRecord(str(uuid4()),item.id,item.current_revision_id,actor_id,t,changelog.strip()); self.repo.save_publication(rec)
        self.repo.complete_assignment(item.id,AssignmentStage.PUBLICATION)
        out=self._save_transition(item,replace(item,state=EditorialState.PUBLISHED,published_revision_id=item.current_revision_id,updated_at=t))
        self._audit(actor_id,'editorial.item.published',item.id,{'revision_id':item.current_revision_id,'changelog':changelog.strip()}); return out
    def archive(self, *, actor_id:str,item_id:str,expected_version:int|None=None):
        self._require(actor_id, EditorialRole.PUBLISHER); item=self._item(item_id); self._assert_expected(item,expected_version)
        t=self.now()
        if self.projector is not None and hasattr(self.projector,'archive'): self.projector.archive(item=item,archived_at=t)
        out=self._save_transition(item,replace(item,state=EditorialState.ARCHIVED,updated_at=t)); self._audit(actor_id,'editorial.item.archived',item.id); return out
    def add_source(self, *, actor_id:str, item_id:str, filename:str, checksum_sha256:str, mime_type:str|None=None, size_bytes:int|None=None, storage_locator:str|None=None, ocr_confidence:float|None=None):
        self._require(actor_id, EditorialRole.EDITOR); self._item(item_id)
        checksum=checksum_sha256.strip().lower()
        if len(checksum)!=64 or any(c not in '0123456789abcdef' for c in checksum): raise ValueError('sha256_required')
        existing=self.repo.find_source_by_checksum(checksum)
        if existing and existing.item_id!=item_id: raise ValueError('duplicate_source_checksum')
        src=EditorialSource(str(uuid4()),item_id,filename.strip(),mime_type,checksum,size_bytes,storage_locator,ocr_confidence,False,actor_id,self.now())
        self.repo.save_source(src); self._audit(actor_id,'editorial.source.added',item_id,{'source_id':src.id,'ocr_confidence':ocr_confidence}); return src
    def verify_source(self, *, actor_id:str, source_id:str):
        self._require(actor_id, EditorialRole.REVIEWER, EditorialRole.EDITOR)
        src=self.repo.get_source(source_id)
        if not src: raise ValueError('source_not_found')
        if src.imported_by==actor_id and src.ocr_confidence is not None:
            raise ValueError('source_verification_requires_second_person')
        verified=replace(src,human_verified=True); self.repo.save_source(verified); self._audit(actor_id,'editorial.source.verified',src.item_id,{'source_id':src.id}); return verified
    def assign(self, *, actor_id:str,item_id:str,assignee_id:str,stage:AssignmentStage,due_at:datetime|None=None):
        self._require(actor_id,EditorialRole.OWNER); self._item(item_id)
        if stage==AssignmentStage.REVIEW and self._item(item_id).state!=EditorialState.IN_REVIEW: raise ValueError('review_assignment_requires_in_review')
        if stage==AssignmentStage.PUBLICATION and self._item(item_id).state!=EditorialState.APPROVED: raise ValueError('publication_assignment_requires_approved')
        target=self.repo.get_member(assignee_id)
        if not target or not target.active: raise ValueError('assignee_not_active')
        expected={AssignmentStage.REVIEW:{EditorialRole.REVIEWER,EditorialRole.OWNER},AssignmentStage.PUBLICATION:{EditorialRole.PUBLISHER,EditorialRole.OWNER},AssignmentStage.EDITING:{EditorialRole.EDITOR,EditorialRole.OWNER}}[stage]
        if target.role not in expected: raise ValueError('assignee_role_mismatch')
        a=EditorialAssignment(str(uuid4()),item_id,stage,assignee_id,actor_id,due_at,True,self.now()); self.repo.save_assignment(a); self._audit(actor_id,'editorial.assignment.updated',item_id,{'assignee_id':assignee_id,'stage':stage.value,'due_at':due_at.isoformat() if due_at else None}); return a
    def set_member(self, *, actor_id:str, account_id:str, role:EditorialRole, active:bool=True):
        self._require(actor_id, EditorialRole.OWNER)
        if actor_id==account_id and (not active or role!=EditorialRole.OWNER): raise ValueError('owner_cannot_remove_own_owner_role')
        member=EditorialMember(account_id=account_id,role=role,active=active); self.repo.save_member(member); self._audit(actor_id,'editorial.member.updated',account_id,{'role':role.value,'active':active}); return member
    def members(self, actor_id:str): self._require(actor_id, EditorialRole.OWNER); return self.repo.list_members()
    def quality_gates(self, actor_id:str,item_id:str,phase:str='review'):
        self._member(actor_id); item=self._item(item_id); rev=self.repo.get_revision(item.current_revision_id) if item.current_revision_id else None; sources=self.repo.list_sources(item.id)
        rights_review=item.rights_status not in {RightsStatus.UNKNOWN,RightsStatus.RESTRICTED}
        rights_publish=item.rights_status in {RightsStatus.AUTHORIZED,RightsStatus.PUBLIC_DOMAIN}
        ocr_ok=all(s.ocr_confidence is None or s.human_verified for s in sources)
        src_ok=bool(rev and rev.source_fingerprint.strip()) if item.risk in {RiskLevel.MEDICAL,RiskLevel.HIGH_STAKES} else True
        ai_ok=bool(not rev or not rev.ai_generated or (rev.prompt_version or '').strip())
        gates=[QualityGateResult('revision_required',rev is not None,'Révision courante','Une révision est nécessaire.'),QualityGateResult('distribution_rights_not_cleared',rights_publish if phase=='publish' else rights_review,'Droits de diffusion','Les droits doivent être documentés.'),QualityGateResult('ocr_source_requires_human_verification',ocr_ok,'OCR vérifié','Tout OCR doit être vérifié humainement.'),QualityGateResult('high_risk_source_required',src_ok,'Traçabilité des sources','Les contenus à risque élevé doivent être sourcés.'),QualityGateResult('ai_prompt_version_required',ai_ok,'Provenance IA','La version du prompt doit être conservée.')]
        if phase=='publish' and rev:
            approved=[r for r in self.repo.list_reviews(item.id) if r.revision_id==rev.id and r.decision=='approved']
            gates.append(QualityGateResult('approved_review_required',bool(approved),'Relecture approuvée','La révision doit avoir une approbation valide.'))
        return tuple(gates)
    def detail(self, actor_id:str,item_id:str):
        self._member(actor_id); item=self._item(item_id)
        audit=tuple(self.audit.list_for_entity(entity_type='editorial_item',entity_id=item_id,limit=200)) if self.audit and hasattr(self.audit,'list_for_entity') else ()
        return {'item':item,'revisions':self.repo.list_revisions(item_id),'sources':self.repo.list_sources(item_id),'reviews':self.repo.list_reviews(item_id),'publications':self.repo.list_publications(item_id),'assignments':self.repo.list_assignments(item_id=item_id),'review_gates':self.quality_gates(actor_id,item_id,'review'),'publish_gates':self.quality_gates(actor_id,item_id,'publish'),'audit':audit}
    def search(self, actor_id:str, **filters): self._member(actor_id); return self.repo.search_items(**filters)
    def dashboard(self, actor_id:str):
        self._member(actor_id); items=self.repo.list_items(limit=1000); counts={s.value:0 for s in EditorialState}
        for i in items: counts[i.state.value]+=1
        assignments=self.repo.list_assignments(active_only=True); now=self.now(); overdue=sum(1 for a in assignments if a.due_at and a.due_at<now)
        mine=sum(1 for a in assignments if a.assignee_id==actor_id)
        return {'counts':counts,'total':len(items),'needs_review':counts['in_review'],'changes_requested':counts['changes_requested'],'approved_to_publish':counts['approved'],'active_assignments':len(assignments),'overdue_assignments':overdue,'my_assignments':mine}
    def _item(self,item_id):
        item=self.repo.get_item(item_id)
        if not item: raise ValueError('editorial_item_not_found')
        return item
    def _audit(self,actor,action,item_id,metadata=None):
        if self.audit: self.audit.write(actor_id=actor,action=action,entity_type='editorial_item',entity_id=item_id,metadata=metadata or {})
