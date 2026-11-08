from __future__ import annotations

import base64
import hashlib
import json

from app.modules.library.application.ports import LibraryAccessPort, LibraryRepository, ResourceDeliveryPort
from app.modules.library.domain.model import CatalogPage, LibraryCourse, ResourceManifestItem


class LibraryService:
    def __init__(self, repository: LibraryRepository, access: LibraryAccessPort, delivery: ResourceDeliveryPort) -> None:
        self.repository = repository
        self.access = access
        self.delivery = delivery

    def list_catalog(self, **filters) -> tuple[LibraryCourse, ...]:
        return tuple(c for c in self.repository.list_courses(**filters) if c.publication_state.value == "published")


    def catalog_page(self, *, faculty_domain=None, program=None, level=None, semester=None, query=None, cursor=None, limit=100) -> CatalogPage:
        offset = self._decode_cursor(cursor)
        limit = max(1, min(int(limit), 200))
        rows = self.repository.list_courses_page(
            faculty_domain=faculty_domain, program=program, level=level, semester=semester, query=query,
            offset=offset, limit=limit + 1,
        )
        has_more = len(rows) > limit
        page_rows = tuple(rows[:limit])
        next_cursor = self._encode_cursor(offset + limit) if has_more else None
        count, latest = self.repository.catalog_revision(
            faculty_domain=faculty_domain, program=program, level=level, semester=semester, query=query,
        )
        material = {"filters":[faculty_domain, program, level, semester, query], "count":count, "latest":latest}
        etag = '"' + hashlib.sha256(json.dumps(material, ensure_ascii=False, separators=(",",":"), sort_keys=True).encode()).hexdigest()[:32] + '"'
        return CatalogPage(courses=page_rows, next_cursor=next_cursor, etag=etag)

    @staticmethod
    def _encode_cursor(offset: int) -> str:
        return base64.urlsafe_b64encode(str(max(0, offset)).encode()).decode().rstrip("=")

    @staticmethod
    def _decode_cursor(cursor: str | None) -> int:
        if not cursor:
            return 0
        try:
            padded = cursor + "=" * (-len(cursor) % 4)
            value = int(base64.urlsafe_b64decode(padded.encode()).decode())
        except Exception as exc:
            raise ValueError("invalid_library_cursor") from exc
        if value < 0 or value > 10_000_000:
            raise ValueError("invalid_library_cursor")
        return value

    def get_course(self, course_id: str) -> LibraryCourse:
        course = self.repository.get_course(course_id)
        if course is None or course.publication_state.value != "published":
            raise ValueError("library_course_not_found")
        return course

    def manifest(self, *, account_id: str, course_id: str) -> dict:
        course = self.get_course(course_id)
        if not course.active_version_id:
            raise ValueError("library_course_has_no_active_version")
        version = self.repository.get_version(course.active_version_id)
        if version is None:
            raise ValueError("library_course_version_not_found")
        premium = self.access.is_premium(account_id)
        items = []
        for r in self.repository.list_resources(version.id):
            locked = (course.premium_required or r.premium_required) and not premium
            token = None if locked else self.delivery.create_delivery_token(account_id=account_id, resource=r)
            items.append(ResourceManifestItem(
                id=r.id, kind=r.kind, title=r.title, mime_type=r.mime_type, size_bytes=r.size_bytes,
                checksum_sha256=r.checksum_sha256, premium_required=(course.premium_required or r.premium_required),
                offline_allowed=(r.offline_allowed and not locked), access="locked" if locked else "available",
                delivery_token=token,
            ))
        return {"course": course, "version": version, "resources": tuple(items), "premium": premium}
