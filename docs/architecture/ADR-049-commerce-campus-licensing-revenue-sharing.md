# ADR-049 — LOT 29 Commerce, Mobile Money, Campus Licensing & Revenue Sharing

## Decision
EduNova keeps Mobile Money behind provider adapters and never trusts a client-side payment assertion. Webhooks are signed, deduplicated and settled atomically. Individual Premium remains entitlement-led and reversible through subscription grants.

LOT 29 adds institutional commercial primitives: Campus licenses with seats, term and grace window; append-only commercial ledger; revenue partners; basis-point revenue-share rules; and reconcilable partner settlements. Campus commercial administration is limited to OWNER/RECTOR/ADMIN roles.

Prices remain configurable. The product does not hard-code a commercial promise to a specific operator or aggregator. Production adapters, provider credentials, real settlement/reconciliation and financial/legal validation remain OPEN-machine/provider.
