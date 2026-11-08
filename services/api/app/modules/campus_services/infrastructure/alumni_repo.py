"""Scoped and opt-in alumni records; unverified claims are never public."""
from datetime import UTC
from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, UniqueConstraint, select, update
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.infrastructure.database import Base


def iso(value):
    return (value if value.tzinfo else value.replace(tzinfo=UTC)).isoformat()


class AlumniProfileRow(Base):
    __tablename__ = 'campus_alumni_profiles'
    __table_args__ = (
        UniqueConstraint('institution_id', 'account_id', name='uq_alumni_tenant_account'),
        CheckConstraint('graduation_year BETWEEN 1950 AND 2100', name='ck_alumni_year'),
        CheckConstraint("status IN ('pending','verified','rejected')", name='ck_alumni_status'),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(64), index=True)
    account_id: Mapped[str] = mapped_column(String(64))
    display_name: Mapped[str] = mapped_column(String(160))
    program_name: Mapped[str] = mapped_column(String(160))
    graduation_year: Mapped[int] = mapped_column(Integer)
    headline: Mapped[str] = mapped_column(String(240), default='')
    visible: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(24), default='pending')
    verification_reference: Mapped[str] = mapped_column(String(160), default='')
    reviewed_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    row_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True))


class AlumniOpportunityRow(Base):
    __tablename__ = 'campus_alumni_opportunities'
    __table_args__ = (CheckConstraint("state IN ('published','withdrawn')", name='ck_alumni_opportunity_state'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    institution_id: Mapped[str] = mapped_column(String(64), index=True)
    posted_by: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(String(2000))
    application_url: Mapped[str] = mapped_column(String(500), default='')
    state: Mapped[str] = mapped_column(String(24))
    row_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True))


def profile_dict(p, private=False):
    data = dict(id=p.id, institution_id=p.institution_id, display_name=p.display_name,
                program_name=p.program_name, graduation_year=p.graduation_year,
                headline=p.headline, status=p.status, visible=p.visible,
                row_version=p.row_version)
    if private:
        data['account_id'] = p.account_id
        # Reference is never returned to directory viewers.
        data['reviewed_by'] = p.reviewed_by
    return data


def opportunity_dict(o):
    return dict(id=o.id, institution_id=o.institution_id, title=o.title,
                description=o.description, application_url=o.application_url,
                state=o.state, row_version=o.row_version, created_at=iso(o.created_at))


class SqlCampusAlumniRepository:
    def __init__(self, sf):
        self.sf = sf

    def verified_institutions(self, account):
        """Only tenant IDs for THIS account's own verified alumni profiles.

        No global tenant listing; status and visibility of other users are never
        queried. Eligibility is rechecked against current campus state by service.
        """
        with self.sf() as session:
            return tuple(session.scalars(select(AlumniProfileRow.institution_id).where(
                AlumniProfileRow.account_id == account,
                AlumniProfileRow.status == 'verified').order_by(
                AlumniProfileRow.institution_id).limit(500)).all())

    def own(self, institution, account):
        with self.sf() as session:
            row = session.scalar(select(AlumniProfileRow).where(
                AlumniProfileRow.institution_id == institution,
                AlumniProfileRow.account_id == account))
            return profile_dict(row, private=True) if row else None

    def apply(self, institution, account, data, expected_version, now):
        from uuid import uuid4
        with self.sf.begin() as session:
            row = session.scalar(select(AlumniProfileRow).where(
                AlumniProfileRow.institution_id == institution,
                AlumniProfileRow.account_id == account).with_for_update())
            if row is None:
                if expected_version != 0:
                    raise ValueError('alumni_profile_concurrent_conflict')
                row = AlumniProfileRow(id='alm_'+uuid4().hex, institution_id=institution,
                    account_id=account, status='pending', verification_reference='',
                    reviewed_by=None, row_version=1, created_at=now, updated_at=now, **data)
                session.add(row)
            else:
                if row.row_version != expected_version:
                    raise ValueError('alumni_profile_concurrent_conflict')
                for key, value in data.items():
                    setattr(row, key, value)
                row.status = 'pending'
                row.verification_reference = ''
                row.reviewed_by = None
                row.row_version += 1
                row.updated_at = now
            session.flush()
            return profile_dict(row, private=True)

    def decide(self, institution, profile_id, actor, version, status, reference, now):
        with self.sf.begin() as session:
            row = session.scalar(select(AlumniProfileRow).where(
                AlumniProfileRow.id == profile_id,
                AlumniProfileRow.institution_id == institution).with_for_update())
            if row is None:
                raise ValueError('alumni_profile_not_found')
            if row.account_id == actor:
                raise PermissionError('alumni_self_verification_forbidden')
            if row.status != 'pending' or row.row_version != version:
                raise ValueError('alumni_profile_concurrent_conflict')
            row.status = status
            row.verification_reference = reference
            row.reviewed_by = actor
            row.visible = row.visible and status == 'verified'
            row.row_version += 1
            row.updated_at = now
            session.flush()
            return profile_dict(row, private=True)

    def directory(self, institution):
        with self.sf() as session:
            rows = session.scalars(select(AlumniProfileRow).where(
                AlumniProfileRow.institution_id == institution,
                AlumniProfileRow.visible.is_(True),
                AlumniProfileRow.status == 'verified').order_by(AlumniProfileRow.display_name).limit(200)).all()
            return [profile_dict(row) for row in rows]

    def pending(self, institution):
        with self.sf() as session:
            rows = session.scalars(select(AlumniProfileRow).where(
                AlumniProfileRow.institution_id == institution,
                AlumniProfileRow.status == 'pending').order_by(AlumniProfileRow.created_at).limit(200)).all()
            return [profile_dict(row, private=True) for row in rows]

    def opportunities(self, institution):
        with self.sf() as session:
            rows = session.scalars(select(AlumniOpportunityRow).where(
                AlumniOpportunityRow.institution_id == institution,
                AlumniOpportunityRow.state == 'published').order_by(AlumniOpportunityRow.created_at.desc()).limit(200)).all()
            return [opportunity_dict(row) for row in rows]

    def post_opportunity(self, institution, actor, title, description, url, now):
        from uuid import uuid4
        with self.sf.begin() as session:
            row = AlumniOpportunityRow(id='alo_'+uuid4().hex, institution_id=institution,
                posted_by=actor, title=title, description=description,
                application_url=url, state='published', row_version=1,
                created_at=now, updated_at=now)
            session.add(row)
            session.flush()
            return opportunity_dict(row)

    def withdraw_opportunity(self, institution, id, version, now):
        with self.sf.begin() as session:
            row = session.scalar(select(AlumniOpportunityRow).where(
                AlumniOpportunityRow.id == id,
                AlumniOpportunityRow.institution_id == institution).with_for_update())
            if row is None or row.state != 'published' or row.row_version != version:
                raise ValueError('alumni_opportunity_concurrent_conflict')
            row.state = 'withdrawn'
            row.row_version += 1
            row.updated_at = now
            session.flush()
            return opportunity_dict(row)
