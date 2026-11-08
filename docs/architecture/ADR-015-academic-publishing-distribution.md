# ADR-015 — Academic Publishing & Catalog Distribution

LOT 14 separates editorial approval from catalog release. Studio governance remains authoritative; the publication module accepts only the exact revision already published by Studio. A release is a versioned distribution decision with academic placement, audience, rollout, entitlement and offline policy. Publication produces a canonical immutable SHA-256 snapshot. Withdrawal is explicit and audited; historical snapshots are never rewritten.

University is optional placement context, never a tenant assumption. Core placement remains faculty/domain → program → curriculum version → level → semester → UE/ECUE/subject.
