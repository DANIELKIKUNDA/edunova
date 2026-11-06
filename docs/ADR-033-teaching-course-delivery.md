# ADR-033 — Teaching & Course Delivery bounded context

LOT 23 introduces an institutional teaching bounded context on top of Campus Core. A course is the catalog identity; an offering binds it to a cohort and academic period. Teacher assignments grant offering-scoped write authority. Sessions form the institutional cahier de texte; resources are draft-first and explicitly published. Students only see published offerings tied to an active cohort enrollment. Tenant identity and membership remain owned by Campus Core. Assignments/submissions, gradebook, attendance and billing are deliberately excluded for LOT 24–29.

Official resources may retain `source_revision` so later EduNova Intelligence extraction can preserve provenance. Intelligence proposals never auto-publish institutional teaching material.
