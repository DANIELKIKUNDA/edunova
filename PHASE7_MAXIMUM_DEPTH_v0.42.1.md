# EduNova v0.42.1 — Phase 7 Mobile Money Maximum Depth

This hardening pass extends the provider-neutral payment gateway without claiming live Orange Money or Airtel Money certification.

## Closed gaps
- Provider event replay-conflict detection: the same provider event id cannot be replayed with a different signed envelope.
- Persistent attempt journal for callback, polling/observation and cancellation operations.
- Provider observations are evidence only: even a polled `succeeded` state cannot credit Student Finance without the authenticated settlement callback path.
- Explicit pending-intent cancellation with reason and audit trail.
- Persistent reconciliation records comparing provider and local status without silently mutating financial truth.
- Operations queue for pending intents with attempts and reconciliation history.
- Migration 0065 adds attempt and reconciliation tables and indexes.

## Certification boundary
This checkpoint certifies local backend contracts and adversarial tests. It does not certify live provider credentials, provider-specific HTTP adapters, production webhook ingress, real network retries, or provider settlement files. Those remain external certification work.
