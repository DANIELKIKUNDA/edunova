# EduNova v0.2.0 — LOT 1 Fondation locale

Cette baseline remplace v0.1.0 comme point de reprise fonctionnel.

## Invariants

1. Document personnel local par défaut.
2. Aucun upload implicite de PDF/photo personnelle.
3. UI -> application -> domaine ; l’UI ne parle pas directement à Drift.
4. Synchronisation future via outbox.
5. Les fournisseurs OCR/IA/paiement restent interchangeables.
6. L’onboarding académique ne rend pas l’université obligatoire.

## Certification disponible dans cet environnement

- Backend Python : `pytest -q`.
- Flutter : non compilable ici car Flutter/Dart ne sont pas installés ; génération Drift + analyse + tests à exécuter sur la machine Flutter via les scripts fournis.
