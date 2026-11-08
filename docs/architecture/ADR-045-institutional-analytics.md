# ADR-045 — Institutional Analytics & Academic Intelligence

LOT 27 introduces a separate `institutional_analytics` bounded context. It is read-only over authoritative Campus, Teaching, Assignments, Gradebook and Campus Operations data.

## Privacy boundary
The repository MUST NOT read Tutor conversations, personal documents, personal study notes, private planner state, or personal learning activity merely because an institution licenses EduNova. Institutional analytics uses institutional records only.

## Metric governance
Every public KPI has a stable code and version. Ratios expose their population/denominator and return `null` rather than inventing a percentage when the denominator is zero. Signals are factual, explainable observations with evidence; they are not automatic judgments about a student or teacher.

## Access
Institutional leadership roles can access institutional scope. Teachers require an explicit offering scope and an active teacher assignment. Students cannot access institutional analytics endpoints.
