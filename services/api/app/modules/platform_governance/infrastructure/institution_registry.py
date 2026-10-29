"""Platform-only institution control state; no access to student records."""
from datetime import UTC
from sqlalchemy import String, Integer, DateTime, select, update, func, or_
from app.modules.campus.infrastructure.sqlalchemy_repo import InstitutionRow
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.infrastructure.database import Base

class PlatformInstitutionControlRow(Base):
    __tablename__ = 'platform_institution_controls'
    institution_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    state: Mapped[str] = mapped_column(String(24), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False)
    changed_by: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)

class InstitutionControlRepository:
    def __init__(self, session_factory): self.sf = session_factory
    @staticmethod
    def serialize(row):
        return {'institution_id':row.institution_id,'state':row.state,'reason':row.reason,
                'row_version':row.row_version,'changed_by':row.changed_by,'updated_at':row.updated_at.isoformat()}
    def list(self):
        with self.sf() as s:
            return [self.serialize(x) for x in s.scalars(select(PlatformInstitutionControlRow).order_by(PlatformInstitutionControlRow.institution_id)).all()]
    def directory(self, *, limit=50, offset=0, state=None, search=None):
        """Institution metadata only: no memberships, student or financial records."""
        with self.sf() as s:
            criteria = []
            if state:
                criteria.append(InstitutionRow.state == state)
            if search:
                term = search.strip().lower()
                criteria.append(or_(func.lower(InstitutionRow.name).contains(term),
                                    func.lower(InstitutionRow.slug).contains(term)))
            base = select(InstitutionRow).where(*criteria)
            total = s.scalar(select(func.count()).select_from(InstitutionRow).where(*criteria)) or 0
            rows = s.scalars(base.order_by(InstitutionRow.name, InstitutionRow.id).limit(limit).offset(offset)).all()
            return {'total': total, 'limit': limit, 'offset': offset, 'items': [
                {'institution_id': x.id, 'name': x.name, 'slug': x.slug,
                 'country_code': x.country_code, 'city': x.city, 'state': x.state,
                 'row_version': x.row_version} for x in rows]}

    def statistics(self):
        """Only aggregated institution counts; never expose tenant personal data."""
        with self.sf() as s:
            counts = dict(s.execute(select(InstitutionRow.state, func.count()).group_by(InstitutionRow.state)).all())
            return {'total': sum(counts.values()), 'active': counts.get('active', 0),
                    'suspended': counts.get('suspended', 0), 'archived': counts.get('archived', 0)}

    def change(self, institution_id, state, reason, actor, now, expected_version):
        with self.sf() as s:
            canonical=s.get(InstitutionRow,institution_id)
            if canonical is None: raise ValueError('campus_institution_not_found')
            if canonical.state == 'archived': raise ValueError('archived_institution_cannot_be_reactivated')
            old=s.get(PlatformInstitutionControlRow,institution_id)
            if old is None:
                if expected_version is not None: raise ValueError('institution_control_concurrent_modification')
                row=PlatformInstitutionControlRow(institution_id=institution_id,state=state,reason=reason,row_version=1,changed_by=actor,updated_at=now)
                s.add(row)
                canonical.state=state;canonical.row_version+=1;canonical.updated_at=now
                s.commit();return self.serialize(row)
            if expected_version is None or old.row_version != expected_version:
                raise ValueError('institution_control_concurrent_modification')
            result=s.execute(update(PlatformInstitutionControlRow).where(
                PlatformInstitutionControlRow.institution_id==institution_id,
                PlatformInstitutionControlRow.row_version==expected_version
            ).values(state=state,reason=reason,row_version=expected_version+1,changed_by=actor,updated_at=now))
            if result.rowcount != 1: s.rollback();raise ValueError('institution_control_concurrent_modification')
            canonical.state=state;canonical.row_version+=1;canonical.updated_at=now
            s.commit()
            return {'institution_id':institution_id,'state':state,'reason':reason,'row_version':expected_version+1,'changed_by':actor,'updated_at':now.isoformat()}
