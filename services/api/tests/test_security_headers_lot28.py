from fastapi.testclient import TestClient
from app.main import app

def test_security_headers_are_present():
 r=TestClient(app).get('/health')
 assert r.headers['x-content-type-options']=='nosniff'
 assert r.headers['x-frame-options']=='DENY'
 assert "frame-ancestors 'none'" in r.headers['content-security-policy']
 assert r.headers['referrer-policy']=='no-referrer'
