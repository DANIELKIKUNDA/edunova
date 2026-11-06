# EduNova v0.51.1 — Phase 16 : bibliothèque physique et circulation

## Base et continuité
- Source canonique : `EduNova_v0.51.0_RC_PHASE16_CAMPUS_PHYSICAL_SERVICES_FOUNDATION.zip`.
- Roadmap inchangée : Phase 16 **EN COURS**, phases précédentes conservées.
- Le catalogue de ressources pédagogiques numériques (`modules/library`) est conservé, **sans reconstruction**.
- Les réservations de salles/laboratoires (`campus_services`) restent intactes.

## Implémentation effective
- Modèles distincts : ouvrage, exemplaire physique, prêt ; suivi des dates d'emprunt, d'échéance (21 jours) et de retour, version optimiste.
- API institutionnelle : créer/lister des ouvrages, ajouter/lister des exemplaires, emprunter/lister/restituer ; compte emprunteur dérivé du jeton, jamais d'un paramètre fourni par le client.
- RBAC : catalogue en lecture aux membres actifs ; création d'ouvrages/exemplaires et validation physique des restitutions réservées aux administrateurs Campus ; auditeur lecture seule ; prêts visibles au seul emprunteur sauf administrateurs/auditeur du même établissement.
- Sécurité tenant : toutes les requêtes filtrent l'institution; FK composées institution+ouvrage/exemplaire dans le schéma pour empêcher de relier des entités inter-universités.
- Concurrence : verrou PostgreSQL de l'exemplaire (FOR UPDATE), test de disponibilité transactionnel et index UNIQUE partiel sur les prêts non restitués ; retour transactionnel avec `row_version` et refus des doublons.
- La disponibilité des exemplaires est calculée côté serveur et incluse dans l'API ; elle n'est pas déduite de la seule liste personnelle des prêts.
- Migration SQL **0087_campus_physical_library_v0_51_1.sql** (3 tables + index), tests de migration actualisés.
- Flutter : API sécurisée, page Bibliothèque physique reliée à l'espace Campus ; catalogue, exemplaires, emprunts, rendus administratifs, réinitialisation d'état lors des changements d'université et du cycle de vie.
- Version backend : `0.51.1`; version de l'application : `0.51.1+16001`.

## Vérification — commandes réellement exécutées
- `PYTHONPATH=services/api python -m pytest -q services/api/tests` : **921 passed in 92.08s**, code retour **0**.
- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_phase16_campus_resources_v0_51_0.py services/api/tests/test_phase16_physical_library_v0_51_1.py services/api/tests/test_migration_contract.py` : **22 passed in 6.04s**.
- `python -m compileall -q services/api/app services/api/tests/test_phase16_physical_library_v0_51_1.py scripts/audit_phase16_physical_library.py` : **PASS**.
- `python scripts/audit_phase16_physical_library.py` : **16/16 PASS**, **contrôles de câblage textuels uniquement**.
- Flutter `flutter analyze`, `flutter test`, `flutter build` : **NON EXÉCUTÉS** (SDK Dart/Flutter absent). Deux tests supplémentaires du gateway Flutter sont écrits, pas exécutés.
- PostgreSQL/Redis/stockage objet réel, vérification de concurrence PostgreSQL multi-processus et appareils réels : **NON EXÉCUTÉS**.
- Les tests SQL utilisent SQLite. Le schéma PostgreSQL n'a pas été appliqué sur un serveur PostgreSQL réel.

## Limites maintenues ouvertes
- Il s'agit d'une circulation physique minimale, pas d'un système complet de bibliothèque : pénalités, prolongations, quotas, inventaire après perte/dégradation, notifications de retard et autorisations de bibliothécaire distinctes sont à préciser et implémenter.
- L'emprunt en libre-service produit directement une ligne de prêt ; une politique de délivrance physique par bibliothécaire ou lecture de code-barres n'est pas encore implémentée.
- Plusieurs requêtes API de lecture restent bornées à 250 lignes ; pagination et recherche à renforcer selon les volumes.
- L'intégration des réservations de salles aux horaires académiques réels, équipements/maintenance, événements et alumni reste à faire.
- Les phases 14 et 15 restent en attente de validation Flutter ; la Phase 16 ne peut être déclarée entièrement clôturée avec SDK absent.

## Décision
**v0.51.1 est un checkpoint de développement backend vérifié localement et frontend intégré non compilé. La Phase 16 reste ouverte.**
