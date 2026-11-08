# EduNova v0.35.1 — Phase 0 closure audit

## Scope
Contradictory audit of the v0.35.0 canonical Medicine baseline before Campus Enterprise implementation.

## Confirmed baseline
- Medicine curriculum remains integrated as the pilot academic vertical.
- Platform governance backend defines seven Volcano Tech roles with explicit least-privilege permissions.
- Backend regression suite is mandatory before promotion of this checkpoint.

## Debt found and closed
1. The seven platform roles existed in the API, but the Flutter administration application remained editorial-Studio centric.
2. Identity login was incorrectly coupled to editorial dashboard authorization, preventing legitimate non-editorial platform roles from entering the admin application.
3. The administration boot/login surfaces still used a placeholder sparkle icon instead of the official EduNova brand in key entry points.
4. An Owner could demote their own platform membership through the role-grant endpoint. The service now rejects owner self-demotion and also protects the last active Owner invariant. Control transfer requires another Owner to perform the demotion.

## Implemented
- Unified admin authentication: identity session first, workspace authorization second.
- Platform workspace routing for Volcano Tech platform memberships; Studio remains available for editorial-only accounts.
- Responsive role-specific platform console driven by server-returned sections and effective permissions.
- Seven French role labels and role-specific module cards.
- Official EduNova logo on admin boot and login.
- Additional platform-governance regression tests for Owner continuity and safe control transfer.

## Certification boundary
Flutter SDK/device execution is not certified in this environment. The Dart implementation is included for machine certification. Backend tests, Python compilation, migration/audit contracts and archive integrity are verified here when the release package is built.

## Next frozen roadmap step
Phase 1: institutional academic core (institution/faculty/department/program/cycle/cohort/academic year/semester/UE/ECUE, versioned curriculum and prerequisites), preserving Medicine as the pilot vertical.
