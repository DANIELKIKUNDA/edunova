"""Pure policy for independent personal Premium and institutional Campus access.

Never derive personal Premium from an institution's licence, or vice versa.
The caller must supply a verified, currently valid institution membership.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class CombinedAccess:
    personal_premium: bool
    campus_access: bool
    campus_institution_id: str | None
    personal_premium_until: datetime | None = None
    campus_access_until: datetime | None = None

    @property
    def tier(self) -> str:
        return "premium" if self.personal_premium else "free"

    def as_dict(self) -> dict[str, bool | str | None]:
        return {
            "personal_tier": self.tier,
            "personal_premium": self.personal_premium,
            "campus_access": self.campus_access,
            "campus_institution_id": self.campus_institution_id,
            "personal_premium_until": self.personal_premium_until.isoformat() if self.personal_premium_until else None,
            "campus_access_until": self.campus_access_until.isoformat() if self.campus_access_until else None,
        }


def resolve_combined_access(
    *,
    now: datetime,
    personal_premium_until: datetime | None,
    verified_active_membership: bool,
    institution_id: str | None,
    campus_license_until: datetime | None,
    campus_institution_active: bool,
    campus_seat_assigned: bool,
) -> CombinedAccess:
    """Fail closed on missing, naive or expired dates and unverified Campus state.

    Dates must be timezone-aware. A licence grace period, if applicable, must
    already have been authorized by the institutional licensing service.
    """
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("timezone_aware_now_required")

    def valid_until(value: datetime | None) -> bool:
        return (
            value is not None
            and value.tzinfo is not None
            and value.utcoffset() is not None
            and value.astimezone(timezone.utc) > now.astimezone(timezone.utc)
        )

    premium = valid_until(personal_premium_until)
    campus = bool(
        institution_id
        and institution_id.strip()
        and verified_active_membership
        and campus_institution_active
        and campus_seat_assigned
        and valid_until(campus_license_until)
    )
    return CombinedAccess(
        premium, campus, institution_id if campus else None,
        personal_premium_until if premium else None,
        campus_license_until if campus else None,
    )
