from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PublicationState(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ResourceKind(StrEnum):
    ORIGINAL = "original"
    STRUCTURED_COURSE = "structured_course"
    SUMMARY = "summary"
    AUDIO = "audio"
    FLASHCARDS = "flashcards"
    QUIZ = "quiz"
    PAST_ASSESSMENT = "past_assessment"
    SOLUTION = "solution"
    OTHER = "other"


@dataclass(frozen=True)
class LibraryCourse:
    id: str
    faculty_domain: str
    program: str
    level: str
    semester: str
    title: str
    slug: str
    description: str
    publication_state: PublicationState
    premium_required: bool
    active_version_id: str | None
    updated_at: datetime


@dataclass(frozen=True)
class CourseVersion:
    id: str
    course_id: str
    label: str
    academic_year: str | None
    source_fingerprint: str
    changelog: str
    published_at: datetime | None


@dataclass(frozen=True)
class LibraryResource:
    id: str
    version_id: str
    kind: ResourceKind
    title: str
    mime_type: str | None
    size_bytes: int | None
    checksum_sha256: str | None
    premium_required: bool
    offline_allowed: bool
    sort_order: int
    storage_locator: str | None = None


@dataclass(frozen=True)
class ResourceManifestItem:
    id: str
    kind: ResourceKind
    title: str
    mime_type: str | None
    size_bytes: int | None
    checksum_sha256: str | None
    premium_required: bool
    offline_allowed: bool
    access: str
    delivery_token: str | None = None


@dataclass(frozen=True)
class CatalogPage:
    courses: tuple[LibraryCourse, ...]
    next_cursor: str | None
    etag: str
