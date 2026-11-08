# ADR-042 — Campus operations and high-security attendance

EduNova uses a rotating, server-signed attendance QR, not a daily/static QR. Default lifetime is 15 seconds. Tokens are scoped to institution + attendance session + server epoch + time slot and are HMAC authenticated. Closing/reopening changes the epoch, invalidating captured tokens.

A QR is only one factor. Institution policy can require a previously bound student device, location radius with accuracy threshold, and network/proximity proof. Signals produce a risk score and `needs_review`; they never automatically accuse a student of fraud. One attendance record per student/session prevents replay. Staff review is audited.

No software-only QR mechanism can prove physical presence against a live accomplice relay. Strong deployments should combine the rotating QR with device attestation and an on-campus proximity signal (managed Wi-Fi/BLE/NFC) validated on real infrastructure. These remain OPEN-machine/provider integrations.
