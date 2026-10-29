# LOT 15 — Final hardening v0.16.1

## Added
- Exam preparation plans with future-date, daily-time and course-scope validation.
- Error Bank review lifecycle: resolved on success, bounded exponential rescheduling on failure.
- Prioritized study recommendations: resume > due errors > spaced-repetition cards.
- Database CHECK constraints for study modes, session states and mastery stages.
- Premium Study Workspace reinforcement with Exam Mode affordance and explicit mastery semantics.

## Governance
Learning signals remain distinct: viewing is not mastery. Recommendations are deterministic and explainable.

## Certification
Backend pytest: 285/285 PASS. LOT15 focused tests: 9/9 PASS. Python compileall: PASS. Flutter remains OPEN-machine.
