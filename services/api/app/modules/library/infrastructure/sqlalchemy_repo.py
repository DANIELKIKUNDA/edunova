from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, select, or_, func
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.library.domain.model import CourseVersion, LibraryCourse, LibraryResource, PublicationState, ResourceKind
from app.shared.infrastructure.database import Base


class LibraryCourseRow(Base):
    __tablename__ = "library_courses"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    faculty_domain: Mapped[str] = mapped_column(String(120), index=True)
    program: Mapped[str] = mapped_column(String(160), index=True)
    level: Mapped[str] = mapped_column(String(80), index=True)
    semester: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(240), index=True)
    slug: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    publication_state: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    premium_required: Mapped[bool] = mapped_column(Boolean, default=False)
    active_version_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class CourseVersionRow(Base):
    __tablename__ = "library_course_versions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    course_id: Mapped[str] = mapped_column(String(64), index=True)
    label: Mapped[str] = mapped_column(String(120))
    academic_year: Mapped[str | None] = mapped_column(String(40), nullable=True)
    source_fingerprint: Mapped[str] = mapped_column(String(128), index=True)
    changelog: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LibraryResourceRow(Base):
    __tablename__ = "library_resources"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    version_id: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[str] = mapped_column(String(48), index=True)
    title: Mapped[str] = mapped_column(String(240))
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    premium_required: Mapped[bool] = mapped_column(Boolean, default=False)
    offline_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    storage_locator: Mapped[str | None] = mapped_column(String(512), nullable=True)


class SqlAlchemyLibraryRepository:
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    def list_courses(self, *, faculty_domain=None, program=None, level=None, semester=None, limit=100):
        with self.session_factory() as session:
            stmt = select(LibraryCourseRow).order_by(LibraryCourseRow.faculty_domain, LibraryCourseRow.program, LibraryCourseRow.level, LibraryCourseRow.title).limit(max(1, min(limit, 500)))
            if faculty_domain: stmt = stmt.where(LibraryCourseRow.faculty_domain == faculty_domain)
            if program: stmt = stmt.where(LibraryCourseRow.program == program)
            if level: stmt = stmt.where(LibraryCourseRow.level == level)
            if semester: stmt = stmt.where(LibraryCourseRow.semester == semester)
            rows = session.scalars(stmt).all()
            return tuple(_course(r) for r in rows)

    def list_courses_page(self, *, faculty_domain=None, program=None, level=None, semester=None, query=None, offset=0, limit=100):
        with self.session_factory() as session:
            stmt = select(LibraryCourseRow).where(LibraryCourseRow.publication_state == PublicationState.PUBLISHED.value)
            if faculty_domain: stmt = stmt.where(LibraryCourseRow.faculty_domain == faculty_domain)
            if program: stmt = stmt.where(LibraryCourseRow.program == program)
            if level: stmt = stmt.where(LibraryCourseRow.level == level)
            if semester: stmt = stmt.where(LibraryCourseRow.semester == semester)
            if query and query.strip():
                pattern = f"%{query.strip()}%"
                stmt = stmt.where(or_(
                    LibraryCourseRow.title.ilike(pattern),
                    LibraryCourseRow.description.ilike(pattern),
                    LibraryCourseRow.program.ilike(pattern),
                    LibraryCourseRow.faculty_domain.ilike(pattern),
                ))
            stmt = stmt.order_by(LibraryCourseRow.updated_at.desc(), LibraryCourseRow.id.asc()).offset(max(0, offset)).limit(max(1, min(limit, 201)))
            rows = session.scalars(stmt).all()
            return tuple(_course(r) for r in rows)

    def catalog_revision(self, *, faculty_domain=None, program=None, level=None, semester=None, query=None):
        with self.session_factory() as session:
            stmt = select(func.count(LibraryCourseRow.id), func.max(LibraryCourseRow.updated_at)).where(LibraryCourseRow.publication_state == PublicationState.PUBLISHED.value)
            if faculty_domain: stmt = stmt.where(LibraryCourseRow.faculty_domain == faculty_domain)
            if program: stmt = stmt.where(LibraryCourseRow.program == program)
            if level: stmt = stmt.where(LibraryCourseRow.level == level)
            if semester: stmt = stmt.where(LibraryCourseRow.semester == semester)
            if query and query.strip():
                pattern=f"%{query.strip()}%"
                stmt=stmt.where(or_(LibraryCourseRow.title.ilike(pattern),LibraryCourseRow.description.ilike(pattern),LibraryCourseRow.program.ilike(pattern),LibraryCourseRow.faculty_domain.ilike(pattern)))
            count, latest = session.execute(stmt).one()
            latest_iso = _utc(latest).isoformat() if latest else None
            return int(count or 0), latest_iso

    def get_course(self, course_id: str):
        with self.session_factory() as session:
            row = session.get(LibraryCourseRow, course_id)
            return _course(row) if row else None

    def get_version(self, version_id: str):
        with self.session_factory() as session:
            row = session.get(CourseVersionRow, version_id)
            return _version(row) if row else None


    def get_resource(self, resource_id: str):
        with self.session_factory() as session:
            row = session.get(LibraryResourceRow, resource_id)
            return _resource(row) if row else None

    def get_course_for_version(self, version_id: str):
        with self.session_factory() as session:
            version = session.get(CourseVersionRow, version_id)
            if version is None:
                return None
            row = session.get(LibraryCourseRow, version.course_id)
            return _course(row) if row else None

    def list_resources(self, version_id: str):
        with self.session_factory() as session:
            rows = session.scalars(select(LibraryResourceRow).where(LibraryResourceRow.version_id == version_id).order_by(LibraryResourceRow.sort_order, LibraryResourceRow.id)).all()
            return tuple(_resource(r) for r in rows)

    def save_course(self, c: LibraryCourse) -> None:
        with self.session_factory() as session:
            session.merge(LibraryCourseRow(id=c.id, faculty_domain=c.faculty_domain, program=c.program, level=c.level, semester=c.semester, title=c.title, slug=c.slug, description=c.description, publication_state=c.publication_state.value, premium_required=c.premium_required, active_version_id=c.active_version_id, updated_at=c.updated_at))
            session.commit()

    def save_version(self, v: CourseVersion) -> None:
        with self.session_factory() as session:
            session.merge(CourseVersionRow(id=v.id, course_id=v.course_id, label=v.label, academic_year=v.academic_year, source_fingerprint=v.source_fingerprint, changelog=v.changelog, published_at=v.published_at))
            session.commit()

    def save_resource(self, r: LibraryResource) -> None:
        with self.session_factory() as session:
            session.merge(LibraryResourceRow(id=r.id, version_id=r.version_id, kind=r.kind.value, title=r.title, mime_type=r.mime_type, size_bytes=r.size_bytes, checksum_sha256=r.checksum_sha256, premium_required=r.premium_required, offline_allowed=r.offline_allowed, sort_order=r.sort_order, storage_locator=r.storage_locator))
            session.commit()


def _utc(dt):
    if dt is None: return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def _course(r):
    return LibraryCourse(id=r.id, faculty_domain=r.faculty_domain, program=r.program, level=r.level, semester=r.semester, title=r.title, slug=r.slug, description=r.description, publication_state=PublicationState(r.publication_state), premium_required=r.premium_required, active_version_id=r.active_version_id, updated_at=_utc(r.updated_at))


def _version(r):
    return CourseVersion(id=r.id, course_id=r.course_id, label=r.label, academic_year=r.academic_year, source_fingerprint=r.source_fingerprint, changelog=r.changelog, published_at=_utc(r.published_at))


def _resource(r):
    return LibraryResource(id=r.id, version_id=r.version_id, kind=ResourceKind(r.kind), title=r.title, mime_type=r.mime_type, size_bytes=r.size_bytes, checksum_sha256=r.checksum_sha256, premium_required=r.premium_required, offline_allowed=r.offline_allowed, sort_order=r.sort_order, storage_locator=r.storage_locator)
