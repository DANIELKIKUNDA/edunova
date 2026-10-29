# ADR-044 — Campus Operations complete bounded context

LOT 26 closes daily academic operations around the already-existing Teaching sessions. Campus Operations owns secure attendance, institutional announcements, absence-justification workflow, operational calendar projections, notifications and operational aggregates. It does not duplicate Teaching, Gradebook or Assignments.

## Decisions
- Missing enrolled students are materialized as absent when attendance closes.
- Absence justification is a human decision workflow; evidence never auto-approves an absence.
- Announcements are scoped, scheduled/published/retractable and audited.
- Calendar changes are first-class auditable events; course/session truth remains in Teaching.
- Campus notifications reuse Engagement; no parallel push stack.
- Operational dashboards expose institutional signals, not private Student/Tutor data.
