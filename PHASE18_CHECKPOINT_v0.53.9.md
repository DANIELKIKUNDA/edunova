# EduNova Phase 18 — v0.53.9

## Security boundary: initial paid Campus issuance

Audited the Campus license creation endpoint after v0.53.8 hardened renewals. The `POST /campus/{institution_id}/licenses` endpoint previously allowed a positive `price_cdf` to provision an ACTIVE license without verified payment. The API now rejects positive-price issuance with HTTP 409 (`verified_payment_required_for_paid_campus_license`) before invoking the provisioning service. Zero-price administrative issuance remains available under existing membership authorization.

## Verification

`PYTHONPATH=services/api python -m pytest -q services/api/tests/test_phase18_paid_renewal_boundary.py services/api/tests/test_phase18_campus_renewal.py services/api/tests/test_commerce_lot29.py` — 27 passed.

## Important remaining limitations

This is a defensive API boundary, NOT an implemented paid Campus checkout or fulfillment. The commercial service's direct `create_license` API and other potential provisioning paths need a dedicated authorization/security review. Administrative zero-price issuance requires a policy decision on who may grant free licenses. No Flutter SDK build, end-to-end payment provider tests, or full backend regression was performed for this checkpoint. Phase 18 remains open.
