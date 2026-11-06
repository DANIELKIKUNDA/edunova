# LOT 14 FINAL — v0.15.1

## Portée
Durcissement final de Academic Publishing & Catalog Distribution, sans extension vers un nouveau domaine métier.

## Frontière irréversible renforcée
Le préflight éditorial est rejoué au moment exact de `publish`, et pas seulement lors de la création du brouillon. Une révocation de droits, un changement d'état Studio ou une révision publiée différente bloque donc la publication.

## Contrat de distribution
Le placement exige `faculty_domain`, `program`, `level`. Un rollout `all` exige 100 %. Un rollout `audience` exige une audience explicite. Une programmation doit être future à la création.

## Intégrité
Chaque publication conserve son manifeste canonique et son SHA-256. `GET /v1/publication/releases/{id}/verify` recalcule le digest et expose `integrity_ok` pour contrôle opérateur/audit.

## Défense PostgreSQL
Migration 0013 : CHECK constraints de rollout/état et index partiels pour scheduler/catalogue.

## Studio UI/UX Premium
Publication Center enrichi : recherche, filtres, KPI, master-detail desktop, bottom-sheet mobile/tablette, dossier de distribution, manifeste sélectionnable, état d'intégrité, empty/error/loading states et garde-fous visibles.

## Certification ChatGPT
- Backend: 276/276 PASS
- compileall: PASS
- audit final LOT14: voir `scripts/audit_lot14_final.py`
- Flutter et infrastructure réelle: OPEN-machine
