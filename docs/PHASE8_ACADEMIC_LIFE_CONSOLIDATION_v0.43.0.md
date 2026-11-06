# EduNova v0.43.0 RC — Phase 8 Academic Life Consolidation

## Objective
Consolidate the existing LOT23–27 academic-life capabilities instead of duplicating teaching, assignments, gradebook, planning, exams and attendance.

## Existing capabilities retained
- Teaching: courses, offerings, teacher assignments, sessions, syllabi/topics, resources/revisions.
- Assignments: workflow, groups, submissions, deterministic grading, similarity review, result publication.
- Gradebook: weighted components, marks, exam sessions, lock/publication/retraction.
- Campus operations: attendance sessions, signed dynamic QR/proximity evidence, absence requests, announcements/calendar.
- Planning: scheduling engine and advanced constraints remain the canonical planning subsystem.

## Consolidation gap closed
Previous modules used Campus cohort enrollment as the principal eligibility boundary. Phase 1–5 later introduced canonical versioned curricula and StudentCourseRegistration snapshots. Phase 8 now connects those generations through Academic Delivery.

### Academic Delivery bridge
- Explicit Offering -> CurriculumCourse binding.
- Binding requires the cohort's published curriculum.
- Curriculum course must belong to that exact curriculum.
- Program and academic-year scope are verified.
- Student access requires an ACTIVE student record, matching cohort/curriculum, active academic registration and canonical StudentCourseRegistration.
- Gradebook student access uses Academic Delivery when runtime integration is enabled.
- Publishing a complete Gradebook result synchronizes the canonical StudentCourseRegistration to VALIDATED or FAILED.
- Attendance scan uses the same canonical eligibility boundary.
- Attendance closure does not auto-mark students absent if they are not eligible for the bound curriculum course.

## Migration
0066_academic_delivery_consolidation_v0_43_0.sql

## Certification
- Full backend: 550/550 PASS.
- Phase 8 targeted tests: 5/5 PASS.
- Migration contract isolated: PASS after explicitly importing the new SQLAlchemy mapping; this caught an order-dependent certification defect.
- compileall: PASS.
- LOT32 global audit: 17/17 PASS.

## Certification boundary
This checkpoint certifies backend/static behavior in the current environment. Flutter device builds, production PostgreSQL concurrency, Redis/object storage and external providers remain machine/external certification items.
