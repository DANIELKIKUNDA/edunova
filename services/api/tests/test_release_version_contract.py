from fastapi.testclient import TestClient

from app.main import app
from app.version import __version__


def test_release_version_is_consistent_across_openapi_and_health():
    client = TestClient(app)
    response = client.get('/health')
    assert response.status_code == 200
    assert app.version == __version__
    assert response.json()['version'] == __version__
