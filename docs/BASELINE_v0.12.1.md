# BASELINE EduNova v0.12.1

Date : 22/09/2026

## Portée
Approfondissement maximal du LOT 11 sur la baseline v0.12.0.

## Invariants
1. EduNova Studio est privé et indépendant des universités.
2. Les rôles sont internes à l'organisation EduNova.
3. Un contenu publié est immuable ; toute évolution crée une nouvelle révision.
4. Une restauration crée une nouvelle révision, jamais un écrasement historique.
5. Les contenus médicaux/high-stakes exigent séparation auteur/relecteur/publicateur.
6. Une source OCR est vérifiée par une seconde personne.
7. Les droits de diffusion sont bloquants avant publication.
8. Les conflits de concurrence sont explicites (`409`), jamais silencieux.
9. L'archivage éditorial d'un cours retire la version active du catalogue public.
10. Toute action sensible reste traçable dans l'audit.

## Versions
- API : 0.12.1
- Flutter mobile : 0.12.1+17
- Flutter admin : 0.12.1+17
- Drift mobile : v16 (inchangé)
- PostgreSQL : migration LOT 11 hardening `0008`
