from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True, slots=True)
class PilotCheck:
    code: str
    label: str
    ready: bool
    blocking: bool = True

@dataclass(frozen=True, slots=True)
class PilotInvitation:
    token: str
    institution_id: str
    role: str
    expires_at: datetime
    used: bool = False
