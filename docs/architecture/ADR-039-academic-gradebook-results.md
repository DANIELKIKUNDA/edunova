# ADR-039 — Institutional gradebook and academic results

LOT 25 introduces a bounded context distinct from LOT 18 practice/exam simulation and LOT 24 assignment grading. A gradebook belongs to one institutional course offering. Its weighted components total exactly 100% before opening. Marks may be imported only from explicitly published LOT 24 assignment results or entered by authorized teaching staff. Student-facing academic results remain private until explicit publication and can be retracted only as an audited mutation.

EduNova distinguishes pedagogical practice scores from institutional academic marks. AI suggestions never become official marks without the validation rules of the source bounded context. Tenant membership, course enrollment, optimistic locking and audit remain mandatory.
