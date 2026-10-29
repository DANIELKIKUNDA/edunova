from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class PlacementState(StrEnum):
    PROPOSED='proposed'
    APPROVED='approved'
    ACTIVE='active'
    COMPLETED='completed'
    CANCELLED='cancelled'

@dataclass(frozen=True)
class Placement:
    id:str
    institution_id:str
    student_id:str
    academic_registration_id:str
    host_name:str
    supervisor_account_id:str
    start_date:str
    end_date:str
    state:PlacementState
    version:int
    created_at:datetime
    updated_at:datetime

@dataclass(frozen=True)
class PlacementLog:
    id:str
    placement_id:str
    student_id:str
    activity_date:str
    description:str
    created_at:datetime
