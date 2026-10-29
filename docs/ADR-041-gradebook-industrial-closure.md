# ADR-041 — Gradebook industrial closure

EduNova v0.26.2 closes LOT25 with explicit deliberation and examination invariants.

- Institutional publication requires a locked deliberation state; an open gradebook cannot be published directly.
- Retraction of already published academic results is an academic-administration action, with a mandatory reason and audit event.
- Examination sessions reject temporal overlap inside the same gradebook and use explicit scheduled → closed/cancelled transitions; cancellation requires a reason.
- Attendance outcome and administrative note are carried end-to-end by the HTTP API rather than being silently dropped.
- PostgreSQL mirrors core score/weight/version invariants and adds result-publication lookup indexes.
- LOT25 still does not own institution-wide transcript/diploma policy beyond the course gradebook boundary.
