# LOT 22 — Enterprise hardening v0.23.1

This checkpoint deepens Campus Core without consuming LOT 23+ responsibilities.

## Security corrections and hardening
- explicit role-assignment matrix; non-owner administrators cannot mint the tenant owner role;
- faculty administrators are mandatory scoped administrators and cannot operate outside their academic-unit subtree;
- scoped member listing prevents cross-faculty directory disclosure to faculty administrators;
- institution suspension blocks Campus mutations while preserving authorized read access;
- academic period hierarchy is structural (`academic_year -> semester/term`, `semester -> term`), not merely date-contained;
- role changes are optimistic-lock protected and audited;
- database CHECK/FK constraints add defense in depth beneath application authorization;
- tenant/scope indexes support future institutional scale.

## Boundary preserved
Course delivery remains LOT 23; assignments LOT 24; grades LOT 25; attendance/communications LOT 26; analytics LOT 27; privacy policy/governance LOT 28. This hardening deliberately strengthens only the Campus identity, hierarchy, tenancy and authorization foundation.
