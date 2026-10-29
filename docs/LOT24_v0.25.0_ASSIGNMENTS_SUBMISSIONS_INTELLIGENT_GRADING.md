# LOT 24 — Assignments, Submissions & Intelligent Grading — v0.25.0

Industrial baseline for institutional coursework. Teachers create individual/group assignments, deadlines, attempt limits and rubrics. Students submit text and attachment references; lateness and attempt number are recorded deterministically.

Grading deliberately separates **proposal** from **final institutional decision**. AI/rule engines may propose a score, criterion feedback and confidence, but complex/open/high-stakes work is not made official until a teacher validates it. Similarity detection creates `needs_review` flags only; it never labels a student as a plagiarist automatically.

Tenant membership, enrollment and teaching assignment are rechecked on every sensitive operation. LOT 25 owns the official academic gradebook and consolidated results; LOT 24 owns assignment-level grading decisions only.
