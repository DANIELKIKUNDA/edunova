# EduNova v0.34.2 — Version Integrity Hardening

## Incident découvert
L'audit contradictoire post-v0.34.1 a détecté une divergence réelle : FastAPI annonçait `0.34.1` dans son contrat OpenAPI tandis que `/health` et son test attendaient encore `0.34.0`. La suite passait parce que le test reproduisait la valeur obsolète.

## Correction
- création de `app/version.py` comme source backend unique (`__version__`) ;
- FastAPI, `/health` et OperationalHealthService consomment désormais cette même valeur ;
- tests de contrat alignés sur la release ;
- Flutter Student/Admin alignés sur `0.34.2+71`.

## Doctrine
Une suite verte ne suffit pas si un test encode lui-même une attente périmée. La certification de récupération inclut donc des contrôles contradictoires de cohérence inter-fichiers et inter-surfaces.

## Statut
Les validations nécessitant Flutter SDK, appareils, PostgreSQL/Redis de production, cloud, fournisseur Mobile Money, charge, pentest externe et recette humaine restent OPEN dans leurs environnements respectifs.
