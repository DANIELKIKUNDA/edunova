import pytest
from app.runtime import runtime
from test_phase3_deep_phase4_admission_center import submitted

def complete_review(account='deep4'):
 admin,inst,x,d=submitted(account);r=runtime.admission_center.intake(admin,inst.id,x.id);runtime.admission_center.review_document(admin,inst.id,r.id,d.id,'accepted');r=runtime.admission_center.mark_complete(admin,inst.id,r.id,r.row_version);return admin,inst,x,r

def test_committee_quorum_vote_tally_and_membership():
 admin,inst,x,r=complete_review('committee');c=runtime.admission_center.create_committee(admin,inst.id,x.campaign_id,'Commission médecine',admin,['member-x'],2)
 runtime.admission_center.vote(admin,inst.id,c.id,r.id,'admit','dossier conforme');t=runtime.admission_center.committee_tally(admin,inst.id,c.id,r.id);assert not t['quorum_met'] and t['counts']['admit']==1
 with pytest.raises(PermissionError):runtime.admission_center.vote('outsider',inst.id,c.id,r.id,'admit')

def test_committee_vote_is_idempotently_replaceable_per_voter():
 admin,inst,x,r=complete_review('revote');c=runtime.admission_center.create_committee(admin,inst.id,x.campaign_id,'Jury',admin,[],1);runtime.admission_center.vote(admin,inst.id,c.id,r.id,'waitlist');runtime.admission_center.vote(admin,inst.id,c.id,r.id,'admit');t=runtime.admission_center.committee_tally(admin,inst.id,c.id,r.id);assert t['votes_cast']==1 and t['counts']['admit']==1

def test_timeline_and_dashboard_are_persistent_operational_views():
 admin,inst,x,r=complete_review('timeline');events=runtime.admission_center.timeline(admin,inst.id,r.id);assert [e.event_type for e in events]==['intake','completed'];d=runtime.admission_center.dashboard(admin,inst.id);assert d['total']>=1 and d['states']['complete']>=1

def test_campaign_capacity_blocks_over_admission():
 admin,inst,x1,r1=complete_review('cap1');campaign=runtime.admissions_catalog_repo.campaign_any(x1.campaign_id)
 # test capacity enforcement without mutating catalog: emulate a one-seat campaign object through repository row
 from sqlalchemy import update
 from app.modules.admissions_catalog.infrastructure.sqlalchemy_repo import AdmissionCampaignRow
 with runtime.sessions() as s:s.execute(update(AdmissionCampaignRow).where(AdmissionCampaignRow.id==campaign.id).values(capacity=1));s.commit()
 runtime.admission_center.decide(admin,inst.id,r1.id,r1.row_version,'admitted')
 # second candidate same campaign
 app=runtime.applications.create('cap2',x1.campaign_id,given_names='C',family_name='Two');doc=runtime.applications.upload('cap2',app.id,'DIPLOME','d.pdf','application/pdf',b'%PDF-1.4\ntwo')
 from test_candidate_applications_phase3 import consent
 consent('cap2',app.id);app=runtime.applications.submit('cap2',app.id,app.row_version);r2=runtime.admission_center.intake(admin,inst.id,app.id);runtime.admission_center.review_document(admin,inst.id,r2.id,doc.id,'accepted');r2=runtime.admission_center.mark_complete(admin,inst.id,r2.id,r2.row_version)
 with pytest.raises(ValueError,match='capacity_reached'):runtime.admission_center.decide(admin,inst.id,r2.id,r2.row_version,'admitted')
