# EduNova v0.40.0 — Phase 5 Student Records & Enrollment

Phase 5 closes the admission-to-student boundary. An admitted application can be matriculated only into a cohort compatible with the admission campaign and bound to the exact published curriculum selected by that campaign.

## Implemented invariants
- Admission review must be `admitted`; matriculation is idempotent by admission review.
- One institutional student record per account and institution; one matricule per institution.
- Matricule allocation is institution/year scoped with atomic sequence increment.
- Candidate identity is snapshotted into the durable student record while the original application remains provenance.
- Student Campus membership is provisioned as active `student`; incompatible active staff membership is rejected rather than silently overwritten.
- Initial Campus enrollment and academic-year registration are created together at the service boundary.
- Cohort/program/year/curriculum compatibility is mandatory.
- Curriculum courses are snapshotted into student course registrations so the student's academic contract survives later catalog evolution.
- Re-enrollment into a later academic year is explicit, idempotent and follows that cohort's bound curriculum.
- Student lifecycle transitions are constrained and audited: active, suspended, withdrawn, graduated, archived.
- Student self-service can read only its own dossier; institutional academic administrators retain governed access.
- Dossier 360 foundation exposes durable identity, matricule, academic registrations, course registrations and timeline.

## Certification boundary
Backend/static certification only. Flutter device builds, PostgreSQL concurrency under production load, real object storage and external providers remain for machine/external certification.
