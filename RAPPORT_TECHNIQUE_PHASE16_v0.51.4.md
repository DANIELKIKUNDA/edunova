# EduNova v0.51.4 — Phase 16 : traitement des exemplaires perdus et détériorés

## Chaîne de confiance et périmètre
- Parent canonique : `EduNova_v0.51.3_RC_PHASE16_TENANT_LIBRARY_POLICIES.zip` ; SHA-256 vérifié : `9de64cea23cef794ce7b83065552e88d778e7bdd8c7559e9e8d02e00e403a4fc`.
- Roadmap EduNova 0–26 strictement inchangée ; **Phase 16 toujours en cours** ; aucun module existant reconstruit.
- Projet avancé à **v0.51.4** (`app/version.py` et `apps/mobile/pubspec.yaml`).

## Fonctionnalités backend réalisées
- Service existant de bibliothèque physique : traitement **perdu** ou **détérioré** d'un prêt actif par un administrateur de l'université ; clôture du prêt et sortie simultanée de l'exemplaire de la circulation dans **une transaction SQL**.
- Conservation de la raison de clôture (`returned`, `lost`, `damaged`), visible dans les API ; les prêts encore ouverts ont une raison NULL. Protection DB empêchant les états contradictoires.
- Statut et version de chaque exemplaire : `serviceable`, `damaged`, `lost`, `withdrawn` ; maintien de la cohérence `active` ↔ `condition` par CHECK SQL. Les anciens exemplaires `active=false` sont marqués `withdrawn`, sans leur inventer un dommage.
- Remise en service d'un exemplaire **détérioré** après réparation, exclusivement par un administrateur ; les exemplaires déclarés **perdus** ne peuvent pas être réactivés par cette opération.
- Vérification optimiste de version (CAS) pour incident ou remise en service, et verrouillages de lignes transactionnels. Contre les doubles déclarations, les restitutions concurrentes et les réutilisations obsolètes.
- API authentifiée `POST /v1/campus-services/institutions/{institution_id}/library/loans/{loan_id}/incident` avec `{expected_version,condition}` et `POST /v1/campus-services/institutions/{institution_id}/library/copies/{copy_id}/restore` avec `{expected_version}`. 
- Isolation strictement par établissement dans les requêtes et restrictions RBAC ; absence de mutation de notes, finances ou décisions du jury.
- Migration nouvelle **0090_campus_library_copy_incidents_v0_51_4.sql**. Tables existantes modifiées sans destruction de données ; contraintes PostgreSQL versionnées.

## Interface Flutter développée (non compilée)
- Gateway existant enrichi avec deux appels authentifiés `no-store` et validation des identifiants de route.
- Écran `Bibliothèque physique` : statut perdu/détérioré visible, déclarations de sinistre avec confirmation, et bouton de réintégration réservé au personnel habilité pour les seuls exemplaires détériorés. Le code existant de gestion de session et de changement d'université a été conservé.
- Deux tests de contrat Flutter ajoutés (payload, tenant, version, entrée invalide) ; **écrits mais NON exécutés**.

## Preuves réellement exécutées
- Régression globale backend : `PYTHONPATH=services/api python -m pytest -q services/api/tests` → **987 passed in 92.85s**, processus terminé avec **code retour 0**. Journal : `REGRESSION_BACKEND_v0.51.4.txt`.
- Test ciblé nouveau + contrat des migrations : **23 passed in 6.12s** ; détail dans `TESTS_CIBLES_v0.51.4.txt`. Nouveaux scénarios backend : 22 cas paramétrés (pytest).
- `python -m compileall -q services/api/app` → PASS.
- ZIP : vérification `ZipFile.testzip` et manifeste SHA-256 pour toutes les entrées répertoriées → PASS lors de la génération.

## Limites et réserves
- **Flutter/Dart absents** : `flutter analyze`, `flutter test` et `flutter build` **NON exécutés**. Pas de clôture complète frontend ou Phase 16.
- **PostgreSQL réel non testé** : migration 0090 non exécutée sur un serveur PG, transactions `FOR UPDATE` / concurrence multiprocessus à certifier ; tests DB locaux avec SQLite.
- La colonne historique `returned_at` est utilisée comme horodatage de fermeture technique pour un prêt marqué perdu/détérioré ; `closure_reason` distingue explicitement restitution réelle et résolution d'incident. Les usages hérités de `returned_at` devront être audités avant tout reporting institutionnel des restitutions physiques.
- Les pertes/dommages sont enregistrés sans facturation automatique ni condamnation de l'emprunteur ; aucune pénalité n'est inventée. La réparation reste une confirmation humaine et n'est pas une preuve d'intervention matérielle.
- Journaux d'audit de domaine produits via composant existant après transaction métier : atomicité globale avec audit **non certifiée**.
- Toujours à approfondir en Phase 16 : notifications de retard, workflow maintenance/inventaire, réservation/planning, événements Campus, Alumni, pagination des grands catalogues, validation Flutter.

**Statut : checkpoint backend local v0.51.4 vérifié ; Phase 16 ouverte ; Phase 17 non commencée.**
