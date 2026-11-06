from __future__ import annotations
from datetime import UTC,datetime,timedelta
from dataclasses import replace
from uuid import uuid4

from app.runtime import runtime
from app.modules.ingestion.domain.model import IngestionJob,JobState


def test_repository_lease_heartbeat_and_recovery():
    now=datetime.now(UTC); bid=f'b-{uuid4()}'; did=f'd-{uuid4()}'; jid=f'j-{uuid4()}'
    # Repository-level contract does not need the parent rows for SQLite because there are no FKs.
    runtime.ingestion_repository.save_job(IngestionJob(jid,bid,did,JobState.PENDING,50,0,3,now,None,None,None,None,None,None,now,now))
    claimed=runtime.ingestion_repository.claim_next_job(worker_id='w1',now=now,lease_seconds=10)
    assert claimed and claimed.id==jid and claimed.state==JobState.LEASED and claimed.attempt==1
    assert runtime.ingestion_repository.heartbeat(job_id=jid,worker_id='w1',now=now+timedelta(seconds=5),lease_seconds=10)
    assert runtime.ingestion_repository.recover_expired_leases(now=now+timedelta(seconds=20))==1
    recovered=runtime.ingestion_repository.get_job(jid); assert recovered.state==JobState.RETRY and recovered.last_error=='worker_lease_expired'

def test_internal_recovery_heals_processing_document_state():
    from app.modules.ingestion.domain.model import IngestionDocument,DocumentState,PreflightStatus,IngestionBatch,BatchDefaults,BatchState
    now=datetime.now(UTC); bid=f'b-{uuid4()}'; did=f'd-{uuid4()}'; jid=f'j-{uuid4()}'
    defaults=BatchDefaults('course','Médecine','Médecine','BAC1','S1','standard','authorized','')
    runtime.ingestion_repository.save_batch(IngestionBatch(bid,'Lease recovery','system',BatchState.RUNNING,defaults,2,'a'*64,now,now,now,None))
    runtime.ingestion_repository.save_document(IngestionDocument(did,bid,'idem','x.pdf','application/pdf','application/pdf',10,'b'*64,'x',1,None,None,DocumentState.PROCESSING,PreflightStatus.PASSED,None,None,now,now,None))
    runtime.ingestion_repository.save_job(IngestionJob(jid,bid,did,JobState.LEASED,50,1,3,now,'dead-worker',now-timedelta(seconds=1),now-timedelta(seconds=10),now-timedelta(seconds=20),None,None,now,now))
    assert runtime.ingestion.recover_expired_leases_internal()>=1
    assert runtime.ingestion_repository.get_document(did).state==DocumentState.QUEUED
