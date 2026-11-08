from datetime import UTC, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.shared.infrastructure.database import Base
from app.modules.library.infrastructure.sqlalchemy_repo import SqlAlchemyLibraryRepository
from app.modules.editorial.infrastructure.library_projector import LibraryPublicationProjector
from app.modules.editorial.domain.model import EditorialItem,EditorialRevision,EditorialState,ContentKind,RiskLevel,RightsStatus

def test_course_projection_creates_catalog_version_and_resources(tmp_path):
    e=create_engine(f"sqlite+pysqlite:///{tmp_path/'p.db'}",connect_args={'check_same_thread':False}); Base.metadata.create_all(e); repo=SqlAlchemyLibraryRepository(sessionmaker(bind=e,expire_on_commit=False)); projector=LibraryPublicationProjector(repo); t=datetime(2026,9,22,tzinfo=UTC)
    item=EditorialItem('i1',ContentKind.COURSE,'Physiologie','Médecine','Médecine humaine','BAC1','S1',EditorialState.APPROVED,RiskLevel.MEDICAL,RightsStatus.AUTHORIZED,'','src','ed',t,t,'r1',None)
    rev=EditorialRevision('r1','i1',1,'{"description":"Cours structuré","premium_required":true,"version_label":"2026.1","academic_year":"2026-2027","resources":[{"kind":"summary","title":"Résumé","checksum_sha256":"abc","offline_allowed":true}]}','src',False,None,'ed',t)
    projector.project(item=item,revision=rev,changelog='Initial',published_at=t)
    c=repo.get_course('editorial-i1'); assert c and c.active_version_id=='r1' and c.premium_required
    v=repo.get_version('r1'); assert v and v.label=='2026.1' and v.academic_year=='2026-2027'
    rs=repo.list_resources('r1'); assert len(rs)==1 and rs[0].title=='Résumé'

def test_archive_hides_projected_course(tmp_path):
    e=create_engine(f"sqlite+pysqlite:///{tmp_path/'a.db'}",connect_args={'check_same_thread':False}); Base.metadata.create_all(e); repo=SqlAlchemyLibraryRepository(sessionmaker(bind=e,expire_on_commit=False)); projector=LibraryPublicationProjector(repo); t=datetime(2026,9,22,tzinfo=UTC)
    item=EditorialItem('i2',ContentKind.COURSE,'Biochimie','Médecine','Médecine humaine','BAC1','S1',EditorialState.APPROVED,RiskLevel.MEDICAL,RightsStatus.AUTHORIZED,'','src','ed',t,t,'r2',None)
    rev=EditorialRevision('r2','i2',1,'{"description":"Cours"}','src',False,None,'ed',t)
    projector.project(item=item,revision=rev,changelog='Initial',published_at=t)
    projector.archive(item=item,archived_at=t)
    c=repo.get_course('editorial-i2'); assert c and c.publication_state.value=='archived'
