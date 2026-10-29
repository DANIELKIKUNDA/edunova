# Rapport technique — EduNova v0.51.0

**Périmètre :** Phase 16 — première livraison effective « ressources physiques du Campus ».

## Architecture et modifications

Le nouveau sous-domaine `services/api/app/modules/campus_services` réutilise le contrat institutionnel de `campus`, le moteur d'authentification et la base SQLAlchemy commune. Les migrations 0001–0085 demeurent inchangées ; la migration **0086** ajoute deux tables (ressources physiques, réservations). Les anciennes interfaces de calendrier, présences, contenu pédagogique numérique et analytics restent en place. L'application Flutter intègre un nouvel écran depuis `CampusPage` et une passerelle dédiée. La version de l'API a été alignée sur **0.51.0**.

## Sûreté de fonctionnement

- Isolation institutionnelle contrôlée à chaque méthode du service et filtrée par `institution_id` au dépôt SQL.
- Une ressource provenant d'un autre tenant ne peut pas être réservée : vérification de l'institution dans le verrou transactionnel sur la ressource.
- Mutations RBAC contrôlées au serveur ; aucun rôle fourni par l'application Flutter ne confère une permission.
- Création d'une réservation et vérification du chevauchement dans **la même transaction** sous verrou du parent ressource pour PostgreSQL (non testé sur PostgreSQL réel ici).
- Les annulations et désactivations utilisent `row_version` ; un état déjà annulé ou un numéro de version obsolète produit un conflit.
- Les étudiants ne peuvent obtenir par API que leurs propres réservations ; l'accès aux ressources nécessite l'appartenance active à une institution active.
- Le client Flutter ne conserve pas d'historique institutionnel dans la base hors ligne et évite de réafficher une réponse d'un périmètre périmé.

## Résultats réels

- Baseline : 900/900 PASS.
- Échec intermédiaire documenté : 911 PASS, 1 FAIL (mise à jour requise de la liste de migrations).
- Après correction : 13/13 ciblés PASS, **912/912 globaux PASS (83,80 s)**.
- `compileall` Python : PASS.
- Tests Flutter du gateway : **non exécutés** (SDK indisponible).
- Concurrence PostgreSQL réelle : **non exécutée**.

## Décision

**v0.51.0 constitue un nouveau checkpoint canonique de développement de Phase 16, PAS une certification ni une clôture de phase.** Les cinq domaines de services Campus ne sont pas entièrement couverts ; voir `CHECKPOINT_PHASE16_v0.51.0.md`.
