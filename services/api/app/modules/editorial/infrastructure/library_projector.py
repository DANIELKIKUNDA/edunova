from __future__ import annotations
import json,re
from app.modules.editorial.domain.model import ContentKind
from app.modules.library.domain.model import LibraryCourse,CourseVersion,LibraryResource,PublicationState,ResourceKind

def _slug(text:str)->str:
    s=re.sub(r'[^a-z0-9]+','-',text.lower()).strip('-')
    return s[:180] or 'course'

class LibraryPublicationProjector:
    """Projects approved editorial COURSE revisions into the public EduNova catalog.
    Other editorial kinds remain governed artifacts and may be attached later as resources.
    """
    def __init__(self, library_repository): self.library=library_repository
    def project(self, *, item, revision, changelog:str, published_at):
        if item.kind != ContentKind.COURSE: return
        payload=json.loads(revision.payload_json or '{}')
        course_id=f"editorial-{item.id}"
        existing=self.library.get_course(course_id)
        course=LibraryCourse(
            id=course_id, faculty_domain=item.faculty_domain, program=item.program, level=item.level,
            semester=item.semester or '', title=item.title, slug=existing.slug if existing else f"{_slug(item.title)}-{item.id[:8]}",
            description=str(payload.get('description','')), publication_state=PublicationState.PUBLISHED,
            premium_required=bool(payload.get('premium_required',True)), active_version_id=revision.id, updated_at=published_at,
        )
        version=CourseVersion(id=revision.id,course_id=course_id,label=str(payload.get('version_label',f"R{revision.revision_no}")),academic_year=payload.get('academic_year'),source_fingerprint=revision.source_fingerprint,changelog=changelog or revision.note,published_at=published_at)
        self.library.save_course(course); self.library.save_version(version)
        for idx,res in enumerate(payload.get('resources',[]) or []):
            kind_raw=str(res.get('kind','other'))
            try: kind=ResourceKind(kind_raw)
            except ValueError: kind=ResourceKind.OTHER
            rid=str(res.get('id') or f"{revision.id}-r{idx+1}")
            self.library.save_resource(LibraryResource(id=rid,version_id=revision.id,kind=kind,title=str(res.get('title') or item.title),mime_type=res.get('mime_type'),size_bytes=res.get('size_bytes'),checksum_sha256=res.get('checksum_sha256'),premium_required=bool(res.get('premium_required',course.premium_required)),offline_allowed=bool(res.get('offline_allowed',True)),sort_order=int(res.get('sort_order',idx)),storage_locator=res.get('storage_locator')))

    def archive(self, *, item, archived_at):
        if item.kind != ContentKind.COURSE: return
        course_id=f"editorial-{item.id}"
        existing=self.library.get_course(course_id)
        if not existing: return
        self.library.save_course(LibraryCourse(
            id=existing.id, faculty_domain=existing.faculty_domain, program=existing.program, level=existing.level,
            semester=existing.semester, title=existing.title, slug=existing.slug, description=existing.description,
            publication_state=PublicationState.ARCHIVED, premium_required=existing.premium_required,
            active_version_id=existing.active_version_id, updated_at=archived_at,
        ))
