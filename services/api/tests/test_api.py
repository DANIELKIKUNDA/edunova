import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_endpoint() -> None:
    response = client.post(
        "/v1/readiness/calculate",
        json={
            "coverage": 1.0,
            "quiz_mastery": 0.75,
            "flashcard_mastery": 0.8,
            "weakness_recovery": 0.6,
        },
    )
    assert response.status_code == 200
    assert response.json()["value"] == 81
