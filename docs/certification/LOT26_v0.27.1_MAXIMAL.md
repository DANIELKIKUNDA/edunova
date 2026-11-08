# EduNova v0.27.1 — LOT 26 Secure Attendance Maximal Hardening

- Rotating QR remains short-lived and signed.
- Added independent signed proximity proof, separate secret and shorter TTL.
- Removed client boolean network proof as trusted security evidence (legacy flag is risk-only).
- Production requires ATTENDANCE_QR_SECRET and ATTENDANCE_PROXIMITY_SECRET.
- Missing/expired/wrong proximity proof => high-risk `needs_review`, not automatic fraud verdict.
- Migration 0043 adds proximity policy constraints and operational index.
- OPEN-machine: real BLE/NFC/Wi-Fi beacon delivery, Android/iOS device attestation, PostgreSQL concurrency, Flutter builds, penetration/relay testing.
