# EduNova v0.48.4 — Phase 13: closure and reassessment hardening

## Implemented

1. An open Student Success support plan blocks administrative closure of its parent case. The existing optimistic version and event timeline remain unchanged when closure is rejected.
2. Reassessment comparisons no longer treat missing attendance records as an improvement from an earlier low attendance rate. Attendance changes are compared only when both snapshots have at least three observations. Published course failure counts are compared only when both snapshots contain published results.
3. Two targeted adversarial regression tests protect these invariants.

## Limitations

This is backend rule hardening, not proof of real-world intervention effectiveness. The evidence snapshots may have different observation windows; cross-period normalized cohort analytics and privacy review remain necessary. Flutter/device, real database infrastructure, and external providers are not certified by Python tests.
