from __future__ import annotations

from datetime import datetime
from typing import Any

# Payloads are JSON only. These names are intentionally rejected everywhere because
# they are typical signs that local/private file state is crossing the cloud boundary.
_FORBIDDEN_KEYS = {
    "localUri", "local_uri", "filePath", "file_path", "absolutePath", "absolute_path",
    "storagePath", "storage_path", "rawBytes", "raw_bytes", "binary", "ocrText", "ocr_text",
    "chunkText", "chunk_text", "personalDocument", "personal_document",
}


def validate_sync_payload(entity_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("sync_payload_must_be_object")
    _reject_private_keys(payload)
    validator = _VALIDATORS.get(entity_type)
    if validator is None:
        # Append-only telemetry evolves more rapidly. It still gets privacy/binary and
        # JSON-size protection; strongly projected entities below get strict schemas.
        return payload
    validator(payload)
    return payload


def _reject_private_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in _FORBIDDEN_KEYS:
                raise ValueError("private_local_field_cannot_sync")
            _reject_private_keys(child)
    elif isinstance(value, list):
        for child in value:
            _reject_private_keys(child)


def _exact_keys(payload: dict[str, Any], required: set[str], optional: set[str] = set()) -> None:
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"sync_payload_missing:{','.join(sorted(missing))}")
    extra = payload.keys() - required - optional
    if extra:
        raise ValueError(f"sync_payload_unknown:{','.join(sorted(extra))}")


def _text(value: Any, *, name: str, minimum: int = 1, maximum: int = 240, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, str) or not (minimum <= len(value.strip()) <= maximum):
        raise ValueError(f"invalid_sync_field:{name}")


def _integer(value: Any, *, name: str, minimum: int, maximum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f"invalid_sync_field:{name}")


def _number(value: Any, *, name: str, minimum: float, maximum: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not minimum <= float(value) <= maximum:
        raise ValueError(f"invalid_sync_field:{name}")


def _iso_datetime(value: Any, *, name: str, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, str):
        raise ValueError(f"invalid_sync_field:{name}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid_sync_field:{name}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"invalid_sync_field:{name}")


def _academic_profile(payload: dict[str, Any]) -> None:
    _exact_keys(payload, {"faculty", "program", "level", "semester"}, {"institution"})
    _text(payload["faculty"], name="faculty", maximum=120)
    _text(payload["program"], name="program", maximum=160)
    _text(payload["level"], name="level", maximum=80)
    _text(payload["semester"], name="semester", maximum=80)
    if "institution" in payload:
        _text(payload["institution"], name="institution", maximum=200, nullable=True)


def _calendar_event(payload: dict[str, Any]) -> None:
    _exact_keys(payload, {"title", "kind", "startsAt"}, {"endsAt", "courseId", "notes"})
    _text(payload["title"], name="title", maximum=240)
    if payload["kind"] not in {"course", "interrogation", "exam", "assignment", "practical", "personal"}:
        raise ValueError("invalid_sync_field:kind")
    _iso_datetime(payload["startsAt"], name="startsAt")
    if "endsAt" in payload:
        _iso_datetime(payload["endsAt"], name="endsAt", nullable=True)
    if "courseId" in payload:
        _text(payload["courseId"], name="courseId", maximum=128, nullable=True)
    if "notes" in payload:
        _text(payload["notes"], name="notes", minimum=0, maximum=2000, nullable=True)


def _timetable_entry(payload: dict[str, Any]) -> None:
    _exact_keys(payload, {"title", "weekday", "startMinute", "endMinute"}, {"courseId", "location"})
    _text(payload["title"], name="title", maximum=240)
    _integer(payload["weekday"], name="weekday", minimum=1, maximum=7)
    _integer(payload["startMinute"], name="startMinute", minimum=0, maximum=1439)
    _integer(payload["endMinute"], name="endMinute", minimum=1, maximum=1440)
    if payload["endMinute"] <= payload["startMinute"]:
        raise ValueError("invalid_sync_field:timetable_range")
    if "courseId" in payload:
        _text(payload["courseId"], name="courseId", maximum=128, nullable=True)
    if "location" in payload:
        _text(payload["location"], name="location", minimum=0, maximum=240, nullable=True)


def _planning_preferences(payload: dict[str, Any]) -> None:
    required = {
        "dailyBudgetMinutes", "maxNotificationsPerDay", "quietStartMinute", "quietEndMinute",
        "maxContinuousMinutes", "breakMinutes", "maxCoursesPerDay", "maxCourseSwitches",
        "targetReadiness", "planningHorizonDays",
    }
    _exact_keys(payload, required)
    _integer(payload["dailyBudgetMinutes"], name="dailyBudgetMinutes", minimum=5, maximum=720)
    _integer(payload["maxNotificationsPerDay"], name="maxNotificationsPerDay", minimum=0, maximum=12)
    _integer(payload["quietStartMinute"], name="quietStartMinute", minimum=0, maximum=1439)
    _integer(payload["quietEndMinute"], name="quietEndMinute", minimum=0, maximum=1439)
    _integer(payload["maxContinuousMinutes"], name="maxContinuousMinutes", minimum=10, maximum=180)
    _integer(payload["breakMinutes"], name="breakMinutes", minimum=0, maximum=60)
    _integer(payload["maxCoursesPerDay"], name="maxCoursesPerDay", minimum=1, maximum=20)
    _integer(payload["maxCourseSwitches"], name="maxCourseSwitches", minimum=0, maximum=30)
    _integer(payload["targetReadiness"], name="targetReadiness", minimum=1, maximum=100)
    _integer(payload["planningHorizonDays"], name="planningHorizonDays", minimum=1, maximum=60)


def _reading_progress(payload: dict[str, Any]) -> None:
    _exact_keys(payload, set(), {"page", "position", "progress", "totalPages", "secondsSpent", "reset"})
    if not payload:
        raise ValueError("sync_payload_empty")
    if "page" in payload: _integer(payload["page"], name="page", minimum=0, maximum=2_000_000)
    if "position" in payload: _integer(payload["position"], name="position", minimum=0, maximum=2_000_000_000)
    if "progress" in payload: _number(payload["progress"], name="progress", minimum=0, maximum=1)
    if "totalPages" in payload: _integer(payload["totalPages"], name="totalPages", minimum=0, maximum=2_000_000)
    if "secondsSpent" in payload: _integer(payload["secondsSpent"], name="secondsSpent", minimum=0, maximum=2_000_000_000)
    if "reset" in payload and not isinstance(payload["reset"], bool): raise ValueError("invalid_sync_field:reset")


def _objective_mastery(payload: dict[str, Any]) -> None:
    _exact_keys(payload, {"mastery", "evidenceCount"})
    _number(payload["mastery"], name="mastery", minimum=0, maximum=1)
    _integer(payload["evidenceCount"], name="evidenceCount", minimum=0, maximum=10_000_000)



def _course_follow(payload: dict[str, Any]) -> None:
    _exact_keys(payload, {"courseId", "followed"})
    _text(payload["courseId"], name="courseId", maximum=128)
    if not isinstance(payload["followed"], bool):
        raise ValueError("invalid_sync_field:followed")

_VALIDATORS = {
    "academic_profile": _academic_profile,
    "calendar_event": _calendar_event,
    "timetable_entry": _timetable_entry,
    "planning_preferences": _planning_preferences,
    "reading_progress": _reading_progress,
    "objective_mastery": _objective_mastery,
    "course_follow": _course_follow,
}
