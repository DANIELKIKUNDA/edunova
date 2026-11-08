from sqlalchemy import BigInteger, DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.infrastructure.database import Base

class PilotInvitationRow(Base):
    __tablename__='pilot_invitations'
    token_hash: Mapped[str]=mapped_column(String(64),primary_key=True)
    institution_id: Mapped[str]=mapped_column(String(64),nullable=False,index=True)
    role: Mapped[str]=mapped_column(String(32),nullable=False)
    expires_at: Mapped[object]=mapped_column(DateTime(timezone=True),nullable=False,index=True)
    used_at: Mapped[object|None]=mapped_column(DateTime(timezone=True),nullable=True)
    created_at: Mapped[object]=mapped_column(DateTime(timezone=True),nullable=False)

class ProductFunnelEventRow(Base):
    __tablename__='product_funnel_events'
    id: Mapped[int]=mapped_column(BigInteger,primary_key=True,autoincrement=True)
    event_name: Mapped[str]=mapped_column(String(80),nullable=False,index=True)
    actor_id: Mapped[str|None]=mapped_column(String(64),nullable=True)
    safe_metadata: Mapped[dict]=mapped_column(JSON,nullable=False,default=dict)
    created_at: Mapped[object]=mapped_column(DateTime(timezone=True),nullable=False,index=True)
