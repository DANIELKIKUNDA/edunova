# LOT 2 — Preuves environnement ChatGPT

Date : 2026-09-20

## Backend/document engine

Commande :

```bash
cd services/api
python -m compileall -q app
pytest -q
```

Résultat : **11 passed**.

Couverture fonctionnelle des tests :

- readiness et abonnement hérités ;
- normalisation et dé-césure ;
- extraction PDF structurée ;
- déterminisme SHA-256 / document ID ;
- chunking ;
- recherche ;
- OCR photo ;
- extraction de questions ;
- suppression sûre d'en-têtes/pieds répétés.

## Limite de preuve

Flutter/Dart n'est pas présent dans cet environnement. Aucun PASS Flutter n'est revendiqué. Voir `LOT2_MACHINE_CERTIFICATION.md`.
