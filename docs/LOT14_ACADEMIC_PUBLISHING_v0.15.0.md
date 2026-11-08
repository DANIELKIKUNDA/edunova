# LOT 14 — Academic Publishing & Catalog Distribution v0.15.0

Industrial publishing layer after LOT 13 and Studio approval.

## Implemented
- strict Publisher/Owner authorization;
- preflight: item/revision consistency, Studio-published exact revision, rights, academic context;
- release lifecycle DRAFT → SCHEDULED/PUBLISHED → WITHDRAWN;
- optimistic row version for publish/withdraw;
- academic placement JSON supporting country/institution optionally plus domain/program/curriculum/level/semester/UE/ECUE/subject;
- audience rules and progressive rollout 1–100%;
- Premium and offline policy per release;
- scheduled publication processor;
- immutable canonical catalog snapshot with SHA-256;
- audit events for create/publish/withdraw;
- Publication Center responsive Studio UI with KPIs, state filters and release cards;
- migration 0012 and REST API `/v1/publication`.

## Non-negotiable governance
LOT 14 never approves editorial content. It distributes only the exact revision already published by LOT 11 governance. University remains optional context, not a hard-coded tenant boundary.
