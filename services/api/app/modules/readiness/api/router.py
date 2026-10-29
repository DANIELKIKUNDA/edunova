from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.modules.readiness.application.use_cases import CalculateReadiness
from app.modules.readiness.domain.model import ReadinessInputs

router = APIRouter()


class ReadinessRequest(BaseModel):
    coverage: float = Field(ge=0, le=1)
    quiz_mastery: float = Field(ge=0, le=1)
    flashcard_mastery: float = Field(ge=0, le=1)
    weakness_recovery: float = Field(ge=0, le=1)


class ReadinessResponse(BaseModel):
    value: int
    label: str
    disclaimer: str = "Indicateur de préparation, pas une prédiction de note."


@router.post("/calculate", response_model=ReadinessResponse)
def calculate_readiness(payload: ReadinessRequest) -> ReadinessResponse:
    result = CalculateReadiness().execute(ReadinessInputs(**payload.model_dump()))
    return ReadinessResponse(value=result.value, label=result.label)
