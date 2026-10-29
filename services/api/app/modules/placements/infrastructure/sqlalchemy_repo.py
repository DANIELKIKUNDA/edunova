from sqlalchemy import String,Integer,DateTime,ForeignKey,UniqueConstraint,select,update
from sqlalchemy.orm import Mapped,mapped_column
from app.shared.infrastructure.database import Base
from app.modules.placements.domain.model import Placement,PlacementLog,PlacementState

class PlacementRow(Base):
    __tablename__='student_placements'
    id:Mapped[str]=mapped_column(String(64),primary_key=True)
    institution_id:Mapped[str]=mapped_column(String(64),index=True)
    student_id:Mapped[str]=mapped_column(String(64),index=True)
    academic_registration_id:Mapped[str]=mapped_column(String(64),index=True)
    host_name:Mapped[str]=mapped_column(String(200))
    supervisor_account_id:Mapped[str]=mapped_column(String(64))
    start_date:Mapped[str]=mapped_column(String(10))
    end_date:Mapped[str]=mapped_column(String(10))
    state:Mapped[str]=mapped_column(String(24))
    version:Mapped[int]=mapped_column(Integer)
    created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
    updated_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class PlacementLogRow(Base):
    __tablename__='student_placement_logs'
    __table_args__=(UniqueConstraint('placement_id','student_id','activity_date',name='uq_placement_daily_log'),)
    id:Mapped[str]=mapped_column(String(64),primary_key=True)
    placement_id:Mapped[str]=mapped_column(String(64),ForeignKey('student_placements.id'),index=True)
    student_id:Mapped[str]=mapped_column(String(64))
    activity_date:Mapped[str]=mapped_column(String(10))
    description:Mapped[str]=mapped_column(String(3000))
    created_at:Mapped[object]=mapped_column(DateTime(timezone=True))
class SqlPlacementRepository:
    def __init__(self,sf):self.sf=sf
    def create(self,p):
        with self.sf() as s:
            s.add(PlacementRow(**{**p.__dict__,'state':p.state.value}));s.commit()
    def get(self,institution,placement_id):
        with self.sf() as s:
            r=s.scalar(select(PlacementRow).where(PlacementRow.id==placement_id,PlacementRow.institution_id==institution))
            return Placement(r.id,r.institution_id,r.student_id,r.academic_registration_id,r.host_name,r.supervisor_account_id,r.start_date,r.end_date,PlacementState(r.state),r.version,r.created_at,r.updated_at) if r else None
    def transition(self,p,expected_version):
        with self.sf() as s:
            result=s.execute(update(PlacementRow).where(PlacementRow.id==p.id,PlacementRow.institution_id==p.institution_id,PlacementRow.version==expected_version).values(state=p.state.value,version=p.version,updated_at=p.updated_at))
            if result.rowcount!=1:s.rollback();raise ValueError('placement_concurrent_modification')
            s.commit()
    def add_log(self,log):
        with self.sf() as s:s.add(PlacementLogRow(**log.__dict__));s.commit()
    def logs(self,placement_id):
        with self.sf() as s:
            return [PlacementLog(r.id,r.placement_id,r.student_id,r.activity_date,r.description,r.created_at) for r in s.scalars(select(PlacementLogRow).where(PlacementLogRow.placement_id==placement_id).order_by(PlacementLogRow.activity_date)).all()]
