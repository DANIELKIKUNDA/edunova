from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.modules.assistant.domain.model import SourceChunk
from app.runtime import runtime

client = TestClient(app)


def _account_headers() -> tuple[str, dict[str, str]]:
    email = f"lot6-{uuid4().hex}@example.com"
    response = client.post(
        "/v1/identity/register",
        json={"display_name": "Lot Six", "password": "StrongPass123", "email": email, "device_name": "pytest"},
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    return response.json()["account_id"], {"Authorization": f"Bearer {token}"}


def test_shared_course_answer_is_cited_and_cached_without_second_charge():
    account_id, headers = _account_headers()
    course_id = f"physio-{uuid4().hex}"
    runtime.knowledge.index_chunks((
        SourceChunk(
            chunk_id=f"chunk-{uuid4().hex}",
            document_id="physiology-pdf",
            course_id=course_id,
            section_title="Potentiel d'action",
            start_page=34,
            end_page=36,
            text="La dépolarisation du potentiel d'action dépend principalement de l'ouverture des canaux sodiques et de l'entrée rapide des ions sodium Na+.",
            score=1.0,
            source_fingerprint="physio-v1",
        ),
    ))
    before = runtime.ai_wallets.get(account_id).balance
    payload = {
        "question": "Quel ion provoque principalement la dépolarisation du potentiel d'action ?",
        "task": "explain",
        "privacy_mode": "shared_course",
        "course_id": course_id,
        "subject_domain": "medicine",
        "language": "fr",
    }
    first = client.post("/v1/assistant/ask", json=payload, headers=headers)
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["abstained"] is False
    assert body["grounded"] is True
    assert body["credits_charged"] == 2  # medical/high reliability route
    assert body["citations"][0]["start_page"] == 34
    after_first = runtime.ai_wallets.get(account_id).balance
    assert after_first == before - 2

    second = client.post("/v1/assistant/ask", json=payload, headers=headers)
    assert second.status_code == 200, second.text
    cached = second.json()
    assert cached["cache_hit"] is True
    assert cached["credits_charged"] == 0
    assert runtime.ai_wallets.get(account_id).balance == after_first


def test_personal_document_requires_explicit_consent_and_is_never_shared_cached():
    account_id, headers = _account_headers()
    payload = {
        "question": "Explique la glycolyse à partir de cet extrait.",
        "task": "simplify",
        "privacy_mode": "personal_document",
        "subject_domain": "biochimie",
        "consent_to_remote_analysis": False,
        "local_context": [{
            "chunk_id": "local-1",
            "document_id": "private-doc-1",
            "section_title": "Glycolyse",
            "start_page": 12,
            "end_page": 13,
            "text": "La glycolyse transforme le glucose en pyruvate et produit de l'ATP et du NADH dans le cytosol.",
        }],
    }
    denied = client.post("/v1/assistant/ask", json=payload, headers=headers)
    assert denied.status_code == 422
    assert denied.json()["detail"] == "remote_analysis_consent_required"
    before = runtime.ai_wallets.get(account_id).balance

    payload["consent_to_remote_analysis"] = True
    first = client.post("/v1/assistant/ask", json=payload, headers=headers)
    assert first.status_code == 200, first.text
    assert first.json()["cache_hit"] is False
    assert first.json()["citations"][0]["document_id"] == "private-doc-1"
    after_first = runtime.ai_wallets.get(account_id).balance
    assert after_first == before - 1

    second = client.post("/v1/assistant/ask", json=payload, headers=headers)
    assert second.status_code == 200, second.text
    assert second.json()["cache_hit"] is False
    assert runtime.ai_wallets.get(account_id).balance == after_first - 1


def test_deterministic_scientific_solution_costs_zero_ai_credit():
    account_id, headers = _account_headers()
    before = runtime.ai_wallets.get(account_id).balance
    response = client.post(
        "/v1/assistant/ask",
        headers=headers,
        json={
            "question": "2*x + 3 = 7",
            "task": "solve_scientific",
            "privacy_mode": "no_document",
            "subject_domain": "mathématiques",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["provider"] == "sympy"
    assert body["credits_charged"] == 0
    assert body["abstained"] is False
    assert runtime.ai_wallets.get(account_id).balance == before


def test_assistant_status_exposes_privacy_contract_not_secrets():
    _, headers = _account_headers()
    response = client.get("/v1/assistant/status", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is True
    assert data["privacy"]["personal_document_cache"] is False
    assert data["privacy"]["personal_document_requires_explicit_consent"] is True
    assert "api_key" not in str(data).lower()
