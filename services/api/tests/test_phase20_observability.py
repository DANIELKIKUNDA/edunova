from __future__ import annotations

import json
import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.shared.infrastructure.observability import JsonFormatter, RequestContextMiddleware


def test_json_formatter_redacts_secrets_and_preserves_structured_context():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        "edunova.worker", logging.ERROR, __file__, 10,
        "job failed token=private-value\nnext-line", (), None,
    )
    record.event = "worker.job.failed"
    record.job_id = "job-123"
    record.attempt = 3

    payload = json.loads(formatter.format(record))

    assert payload["event"] == "worker.job.failed"
    assert payload["job_id"] == "job-123"
    assert payload["attempt"] == 3
    assert "private-value" not in payload["message"]
    assert "[REDACTED]" in payload["message"]
    assert "\n" not in payload["message"]


def test_request_context_rejects_log_injection_request_id_and_returns_safe_id():
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/health")
    def health():
        return {"ok": True}

    response = TestClient(app).get("/health", headers={"X-Request-ID": "bad\nforged"})

    assert response.status_code == 200
    request_id = response.headers["X-Request-ID"]
    assert request_id != "bad\nforged"
    assert len(request_id) == 32


def test_request_context_preserves_valid_correlation_id():
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/health")
    def health():
        return {"ok": True}

    response = TestClient(app).get("/health", headers={"X-Request-ID": "phase20-test-123"})
    assert response.headers["X-Request-ID"] == "phase20-test-123"
