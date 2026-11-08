# EduNova baseline v0.1.0

## Statut

Socle technique initial créé le 20/09/2026.

## Inclus

- Architecture hexagonale documentée.
- Flutter shell premium avec 5 espaces : Accueil, Mes cours, Réviser, Calendrier, Moi.
- Design system clair/sombre.
- Exemple de port repository côté Flutter.
- FastAPI avec domaine pur Readiness et Subscription.
- Ports IA, OCR, paiement et stockage.
- Docker Compose PostgreSQL/Redis/API.
- Tests backend 4/4 PASS.

## Non certifié dans cet environnement

Flutter SDK n'est pas disponible ici. Le code Flutter n'a donc pas encore fait l'objet de `flutter analyze`, `flutter test` ni d'un build Android/Web/Windows/iOS. Le script `scripts/bootstrap_flutter.ps1` effectue cette certification dès que le dépôt est placé sur une machine Flutter.

## Prochain lot recommandé

LOT 1 — Fondation locale : Drift/SQLite, bibliothèque personnelle, import PDF/photo, modèle Document/Course/Assessment, outbox de synchronisation et onboarding réel.
