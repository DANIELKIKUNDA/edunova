from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def register_token():
    email = f"lot5-{uuid4().hex}@example.com"
    r = client.post('/v1/identity/register', json={'display_name':'Lot Five','password':'StrongPass123','email':email,'device_name':'pytest'})
    assert r.status_code == 201, r.text
    return r.json()['access_token']


def test_commerce_requires_authentication():
    r = client.post('/v1/commerce/checkout', json={'plan_code':'premium-30d','phone_number':'+243999000111','provider':'sandbox-mobile-money'}, headers={'Idempotency-Key':'idem-unauth-001'})
    assert r.status_code == 401


def test_full_sandbox_payment_flow_activates_entitlement_and_receipt():
    token = register_token()
    headers = {'Authorization':f'Bearer {token}','Idempotency-Key':f'idem-{uuid4().hex}'}
    checkout = client.post('/v1/commerce/checkout', json={'plan_code':'premium-30d','phone_number':'+243999000111','provider':'sandbox-mobile-money'}, headers=headers)
    assert checkout.status_code == 200, checkout.text
    data = checkout.json()
    event = {
        'event_id': f'evt-{uuid4().hex}',
        'provider_reference': data['provider_reference'],
        'state': 'succeeded',
        'amount': data['amount_cdf'],
        'currency': 'CDF',
        'received_at': datetime.now(UTC).isoformat(),
    }
    wh = client.post('/v1/commerce/webhooks/sandbox-mobile-money', json=event, headers={'x-edunova-sandbox-signature':'valid'})
    assert wh.status_code == 200, wh.text
    auth = {'Authorization':f'Bearer {token}'}
    ent = client.get('/v1/commerce/entitlement', headers=auth)
    assert ent.status_code == 200
    assert ent.json()['premium'] is True
    assert ent.json()['ai_credits_remaining'] >= 25
    receipts = client.get('/v1/commerce/receipts', headers=auth)
    assert receipts.status_code == 200
    assert len(receipts.json()) >= 1
