from __future__ import annotations
import hashlib,json,re
from dataclasses import replace
from datetime import UTC,datetime,timedelta
from uuid import uuid4
from app.modules.editorial.domain.model import EditorialRole
from ..domain.model import *
from .quality import audit_assets

class ContentFactoryService:
    PIPELINE='content-factory-v1.1'; PROMPT='factory-governance-v2'
    DEFAULT_ASSETS=('outline','summary_express','summary_detailed','flashcard','quiz','rag_chunk','concept')
    def __init__(self,repo,ingestion_repo,ingestion_storage,editorial,now=lambda:datetime.now(UTC),audit=None,lease_seconds=300,max_attempts=3): self.repo=repo; self.ingestion_repo=ingestion_repo; self.storage=ingestion_storage; self.editorial=editorial; self.now=now; self.audit=audit; self.lease_seconds=lease_seconds; self.max_attempts=max_attempts
    def _member(self,actor,*roles):
        m=self.editorial._member(actor)
        if roles and m.role not in roles and m.role!=EditorialRole.OWNER: raise PermissionError('content_factory_role_required')
        return m
    def create_run(self,actor_id,document_id,requested_assets=None):
        self._member(actor_id,EditorialRole.EDITOR); result=self.ingestion_repo.get_result_for_document(document_id); doc=self.ingestion_repo.get_document(document_id)
        if not result or not doc: raise ValueError('processed_ingestion_document_required')
        assets=tuple(sorted(set(requested_assets or self.DEFAULT_ASSETS))); invalid=set(assets)-{x.value for x in AssetKind}
        if invalid: raise ValueError('unsupported_factory_asset')
        assets_json=json.dumps(assets,separators=(',',':')); existing=self.repo.find_idempotent(document_id,self.PIPELINE,assets_json)
        if existing:return existing
        batch=self.ingestion_repo.get_batch(doc.batch_id); context=json.dumps({'faculty_domain':batch.defaults.faculty_domain,'program':batch.defaults.program,'level':batch.defaults.level,'semester':batch.defaults.semester,'risk':batch.defaults.risk,'rights_status':batch.defaults.rights_status},sort_keys=True,separators=(',',':'))
        now=self.now(); run=FactoryRun(str(uuid4()),document_id,result.editorial_item_id,actor_id,FactoryState.QUEUED,self.PIPELINE,self.PROMPT,result.artifact_sha256,context,assets_json,now,now,max_attempts=self.max_attempts); self.repo.save_run(run); self._audit(actor_id,'content_factory.run.created',run.id,{'document_id':document_id,'assets':assets}); return run
    def process(self,actor_id,run_id):
        self._member(actor_id,EditorialRole.EDITOR); run=self._run(run_id)
        if run.state==FactoryState.READY_FOR_REVIEW:return run
        if run.state not in {FactoryState.QUEUED,FactoryState.FAILED}: raise ValueError('factory_run_not_processable')
        now=self.now(); run=replace(run,state=FactoryState.PROCESSING,started_at=run.started_at or now,updated_at=now,lease_owner=actor_id,lease_expires_at=now+timedelta(seconds=self.lease_seconds),attempt=run.attempt+1,last_error=None); self.repo.save_run(run)
        try:
            result=self.ingestion_repo.get_result_for_document(run.ingestion_document_id); raw=json.loads(self.storage.read(result.artifact_key).decode('utf-8')); pages=raw.get('pages') or []
            normalized=[{'number':int(p.get('number',i+1)),'text':' '.join(str(p.get('text','')).split())} for i,p in enumerate(pages) if str(p.get('text','')).strip()]
            if not normalized: raise ValueError('factory_source_has_no_usable_text')
            requested=set(json.loads(run.requested_assets_json)); generated=[]
            # Source-grounded deterministic baseline: every generated object carries page evidence.
            for kind,title,payload,pstart,pend,quote,conf in self._generate(normalized,requested):
                canon=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')); a=FactoryAsset(str(uuid4()),run.id,AssetKind(kind),1+sum(1 for x in generated if x.kind.value==kind),title,canon,hashlib.sha256(canon.encode()).hexdigest(),conf,'draft',self.now()); self.repo.save_asset(a); generated.append(a); q=quote[:1200]; self.repo.save_evidence(EvidenceLink(str(uuid4()),run.id,a.id,run.ingestion_document_id,pstart,pend,q,hashlib.sha256(q.encode()).hexdigest(),self.now()))
            gates=self._quality(run,normalized,generated); [self.repo.save_gate(g) for g in gates]; blocking=[g for g in gates if g.severity==GateSeverity.BLOCKING and not g.passed]
            score=max(0,min(100,100-25*len(blocking)-8*sum(1 for g in gates if g.severity==GateSeverity.WARNING and not g.passed)))
            state=FactoryState.FAILED if blocking else FactoryState.READY_FOR_REVIEW; run=replace(run,state=state,completed_at=self.now(),updated_at=self.now(),lease_owner=None,lease_expires_at=None,quality_score=score,last_error='quality_gate_blocked' if blocking else None); self.repo.save_run(run); self._audit(actor_id,'content_factory.run.completed',run.id,{'state':state.value,'quality_score':score,'asset_count':len(generated)}); return run
        except Exception as e:
            failed=replace(run,state=FactoryState.FAILED,updated_at=self.now(),lease_owner=None,lease_expires_at=None,last_error=str(e)[:1000]); self.repo.save_run(failed); raise
    def cancel(self,actor_id,run_id):
        self._member(actor_id,EditorialRole.EDITOR); run=self._run(run_id)
        if run.state in {FactoryState.READY_FOR_REVIEW,FactoryState.CANCELLED}: return run
        if run.state==FactoryState.PROCESSING: raise ValueError('factory_run_processing_cannot_cancel_without_worker_ack')
        run=replace(run,state=FactoryState.CANCELLED,updated_at=self.now(),completed_at=self.now(),lease_owner=None,lease_expires_at=None); self.repo.save_run(run); self._audit(actor_id,'content_factory.run.cancelled',run.id,{}); return run
    def detail(self,actor_id,run_id): self._member(actor_id); r=self._run(run_id); return {'run':r,'assets':self.repo.assets(run_id),'evidence':self.repo.evidence(run_id),'gates':self.repo.gates(run_id)}
    def review_package(self,actor_id,run_id):
        self._member(actor_id); run=self._run(run_id); assets=self.repo.assets(run_id); evidence=self.repo.evidence(run_id); by_asset={e.asset_id:e for e in evidence}
        return {'run':run,'items':tuple({'asset':a,'evidence':by_asset.get(a.id)} for a in assets),'gates':self.repo.gates(run_id),'publication_allowed':False,'required_next_state':'human_review'}
    def list_runs(self,actor_id,limit=100): self._member(actor_id); return self.repo.list_runs(limit)
    def _generate(self,pages,requested):
        alltext=' '.join(p['text'] for p in pages); first=pages[0]; last=pages[-1]; sentences=[s.strip() for s in re.split(r'(?<=[.!?])\s+',alltext) if len(s.strip())>25]; sentences=sentences or [alltext[:1000]]
        if 'outline' in requested:
            heads=[]
            for p in pages:
                line=p['text'].split('. ')[0][:120]; heads.append({'title':line or f"Page {p['number']}",'page':p['number']})
            yield 'outline','Plan structuré',{'sections':heads[:40]},first['number'],last['number'],first['text'],.90
        if 'summary_express' in requested: yield 'summary_express','Résumé express',{'text':' '.join(sentences[:5])[:1800]},first['number'],min(last['number'],first['number']+2),first['text'],.86
        if 'summary_detailed' in requested: yield 'summary_detailed','Résumé détaillé',{'paragraphs':sentences[:20]},first['number'],last['number'],alltext[:1200],.84
        concepts=[]
        words=re.findall(r"\b[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'-]{5,}\b",alltext); freq={w.lower():words.count(w) for w in set(words)}
        for w,_ in sorted(freq.items(),key=lambda x:(-x[1],x[0]))[:12]: concepts.append(w)
        if 'concept' in requested:
            for c in concepts[:8]: yield 'concept',c.title(),{'concept':c,'definition_context':next((s for s in sentences if c in s.lower()),sentences[0])[:600]},first['number'],last['number'],next((s for s in sentences if c in s.lower()),first['text'])[:800],.78
        if 'flashcard' in requested:
            for i,s in enumerate(sentences[:12]): yield 'flashcard',f'Carte {i+1}',{'front':f'Expliquez le point clé {i+1}.','back':s[:700]},first['number'],last['number'],s,.82
        if 'quiz' in requested:
            for i,s in enumerate(sentences[:8]): yield 'quiz',f'Question {i+1}',{'question':f'Quel énoncé résume correctement le point {i+1} ?','answer':s[:700],'explanation':s[:700],'type':'open'},first['number'],last['number'],s,.80
        if 'rag_chunk' in requested:
            for p in pages:
                for j in range(0,len(p['text']),1200):
                    chunk=p['text'][j:j+1400].strip()
                    if len(chunk)>80: yield 'rag_chunk',f"Page {p['number']} · segment {j//1200+1}",{'text':chunk,'page':p['number']},p['number'],p['number'],chunk,.95
    def _quality(self,run,pages,assets):
        now=self.now(); ev=self.repo.evidence(run.id); kinds={a.kind.value for a in assets}; requested=set(json.loads(run.requested_assets_json)); coverage=len(ev)==len(assets) and len(assets)>0
        gates=[QualityGate(str(uuid4()),run.id,'source_text_present',GateSeverity.BLOCKING,bool(pages),'Source OCR/extracted text must exist.',now),QualityGate(str(uuid4()),run.id,'provenance_complete',GateSeverity.BLOCKING,coverage,'Every generated asset must have page-level evidence.',now),QualityGate(str(uuid4()),run.id,'requested_assets_covered',GateSeverity.WARNING,requested.issubset(kinds),'Requested pedagogical families should be generated when source permits.',now),QualityGate(str(uuid4()),run.id,'human_review_required',GateSeverity.INFO,True,'Output ends READY_FOR_REVIEW; publication is never automatic.',now)]
        evidence=self.repo.evidence(run.id)
        for f in audit_assets(assets,evidence,pages):
            severity=GateSeverity.BLOCKING if f.blocking else GateSeverity.WARNING
            gates.append(QualityGate(str(uuid4()),run.id,f.code,severity,f.passed,f.detail,now))
        return gates
    def _run(self,id):
        r=self.repo.get_run(id)
        if not r: raise ValueError('content_factory_run_not_found')
        return r
    def _audit(self,actor,action,id,meta):
        if self.audit:self.audit.write(actor_id=actor,action=action,entity_type='content_factory_run',entity_id=id,metadata=meta)
