# EduNova v0.38.0 — Phase 3 Digital Applications

Phase 3 introduces candidate-owned digital applications on top of the published admissions catalog.

## Implemented
- One idempotent candidate application per account/campaign.
- Draft profile with optimistic locking and strict owner isolation.
- Campaign-open enforcement at creation and final submission.
- Requirement-driven readiness; mandatory document requirements block submission.
- Private application documents stored outside public catalog routes.
- PDF/JPEG/PNG/WebP allow-list plus file-signature verification.
- SHA-256 integrity, duplicate-upload idempotency and replacement history.
- Production malware scanning reuses the ClamAV ingestion boundary; development/test scanner remains explicitly disabled.
- Resumable 24-hour uploads: start, chunk (<=1 MiB), status/recovery, completion, final size/digest verification, chunk cleanup.
- Submitted applications become immutable from the candidate draft API.
- Audit events for creation, edits, upload lifecycle and submission.
- Multi-tenant institution/campaign binding is inherited from the published campaign.

## Explicitly not claimed yet
- Administrative document review, correction requests, admission committee decisions and acceptance/refusal are Phase 4.
- Application-fee settlement is Phase 6/7 and is not faked here.
- Flutter runtime/device certification remains open until machine certification.
- Web research could not be executed from this tool environment; no claim of fresh external verification is made for this checkpoint.

## Verification
- Backend: 506/506 PASS.
- Phase 3 targeted tests: 7/7 PASS.
- LOT32 global audit: 17/17 PASS.
- compileall: PASS.
- Migrations: contiguous through 0057.
