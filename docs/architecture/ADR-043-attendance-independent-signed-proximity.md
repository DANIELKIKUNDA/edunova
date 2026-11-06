# ADR-043 — Independent signed proximity proof

## Decision
LOT 26 v0.27.1 no longer treats a client-supplied `network_proof` boolean as security evidence. When `proximity_mode=signed_beacon`, attendance requires a second, independently signed, session-scoped proof with a 5–30 second TTL in addition to the rotating QR.

The QR secret and proximity secret are distinct and mandatory in production. Both proofs are bound to institution, attendance session and QR epoch. Closing/reopening rotates the epoch and invalidates prior proofs.

## Security boundary
This materially raises the cost of screenshot/photo reuse and simple remote QR forwarding. It does **not** claim absolute relay resistance: a colluding person can attempt real-time relay of every factor. Production deployments should deliver the proximity proof through a local BLE/NFC/Wi-Fi beacon or equivalent trusted local channel and combine it with device attestation where platform support exists. Suspicious evidence produces `needs_review`, never an automatic accusation.
