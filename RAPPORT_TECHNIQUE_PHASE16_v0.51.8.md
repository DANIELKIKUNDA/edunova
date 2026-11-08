# EduNova v0.51.8 — Phase 16 : salles académiques et Alumni

## Provenance et périmètre

Checkpoint parent : `EduNova_v0.51.7_RC_PHASE16_CAMPUS_PERSONAL_ALERTS.zip`.
SHA-256 parent effectivement recalculé : `2561c98e57f6df88edbd900bfc06c3b328083a981342c110ea821c8a07592702`.

La feuille de route v1.0 reste inchangée. Aucune reconstruction des modules existants de calendrier, enseignement ou Campus. Cette version ajoute une liaison aux sessions existantes et un service opt-in d'anciens étudiants.

## Développements et règles métier

### Salles, réservations, calendrier et cours

- Réutilisation des tables canoniques `campus_calendar_events`, `teaching_sessions`, `campus_physical_resources` et `campus_resource_bookings`.
- Tables de liaison *uniquement* : `campus_academic_resource_allocations` (migration 0093) et `campus_teaching_room_allocations` (migration 0095).
- Affectation par personnel institutionnel habilité (OWNER, RECTOR, ADMIN, ACADEMIC_ADMIN) : vérification de la session ou de l'événement, de son état, de l'université et de la nature de la ressource (salle/laboratoire/espace bibliothèque).
- Anti-double-réservation : sur chaque mutation, verrouillage de la ligne de ressource physique avec `SELECT ... FOR UPDATE` sous PostgreSQL, puis vérification dans la même transaction des réservations confirmées, des événements programmés et des séances planifiées. Intervalles semi-ouverts (un événement qui se termine à 12 h n'empêche pas le suivant de commencer à 12 h).
- Libération versionnée (CAS) ; les séances et événements annulés ne bloquent plus les créneaux. Immobilisation pour maintenance interdite lorsqu'une occupation académique future est explicitement affectée.
- API authentifiée : GET/POST `academic-allocations`, `teaching-allocations`, et `/.../<built-in function id>/release` ; audit métier des affectations.

**Limite importante :** les plages non associées explicitement à un identifiant de ressource ne peuvent pas être détectées par leur libellé libre (`location`). C'est une limite de couverture, pas une garantie que toutes les salles historiques sont déjà réconciliées. Concurrence PostgreSQL réelle non certifiée ici.

### Alumni

- Migration 0094 : `campus_alumni_profiles`, `campus_alumni_opportunities`.
- Demande personnelle par compte authentifié, périmètre universitaire et consentement explicite de publication.
- Vérification institutionnelle *manuelle* avec référence interne non exposée dans l'annuaire. L'utilisateur ne peut pas vérifier son propre profil. Les changements de profil annulent l'ancienne validation.
- Annuaire uniquement des profils **verified + visible** ; absence d'e-mail, téléphone ou identité de compte dans les entrées publiques.
- Offres publiques institutionnelles à lien HTTPS facultatif ; publication/retrait uniquement par responsables autorisés, verrou de version.
- Accès de lecture à un ancien étudiant auparavant vérifié sans appartenance académique active, tant qu'il n'existe pas de suspension/révocation explicite.
- Permissions et scopes interuniversitaires négatifs testés ; données du dossier personnel accessibles au seul concerné et aux responsables habilités.

**Limites :** le diplôme n'est pas vérifié automatiquement contre les décisions du jury ni signé électroniquement. La procédure confirme qu'un responsable a consigné une référence ; l'authenticité documentaire reste une validation humaine. L'écran de choix d'établissement pour les diplômés qui n'ont plus d'appartenance active reste un point de parcours à compléter lors de la consolidation UX.

### Flutter / CI

- `campus_academic_resources_page.dart` : visualisation des affectations, liaison/libération au calendrier ou séance, choix de salle, gestion des refus réseau, invalidation des réponses périmées après changement d'université ou cycle de vie.
- `campus_alumni_page.dart` : profil volontaire, liste validée, offres d'emploi, validation admin et révocation du contenu sensible lors des changements de contexte.
- Extension de `CampusServicesGateway`, routeur Flutter et accès depuis l'écran Campus. Pas de stockage offline des dossiers privés ni de bypass des règles backend.
- Tests Dart de contrat des routes, bearer token, CAS et no-store ; pipeline CI : `flutter pub get`, `flutter analyze --no-pub`, `flutter test --no-pub`, `flutter build web --release --no-pub`.

**Flutter SDK et Dart SDK absents du conteneur local.** Les tests, l'analyse Dart et la compilation ne sont donc PAS revendiqués comme exécutés. Le pipeline CI est configuré, mais sa réussite distante n'est pas prouvée. Aucune certification appareil réel, PostgreSQL réel, Redis, stockage objet, fournisseurs externes ou signature légale n'est revendiquée.

## Tests, audit et preuves

| Vérification | Résultat réel |
|---|---|
| Régression backend globale **après toutes les modifications backend** | **1057/1057 PASS**, 236.45 s, exit 0 |
| Tests ciblés Phase 16 et contrat migration (exécution isolée) | 16/16 PASS |
| Compilation syntaxique Python | PASS |
| Audit statique de branchements Flutter / routes / CI | 18/18 PASS (non-compilateur) |
| Analyse YAML du workflow CI | YAML interprétable, PASS |
| Migrations 0093/0094/0095 | Syntaxe exécutée dans un schéma SQLite de contrôle ; PostgreSQL réel non testé |
| `flutter analyze`, `flutter test`, `flutter build web` | **NON EXÉCUTÉS — SDK absent** |

Une exécution intermédiaire de régression, lancée parallèlement à un autre pytest partageant une base SQLite, a produit 54 erreurs et 998 réussites. Ce résultat est **invalidé**, pas présenté comme certification. La régression finale utilise une base dédiée, exécution séquentielle et code de sortie 0.

## Statut

**Phase 16 : approfondissement backend intégré et régression locale verte, frontend code intégré mais vérification Flutter requise.** Ne pas déclarer clôture fonctionnelle définitive. Phase 17 non entamée. Certification appareils/PG réel restent au calendrier de la roadmap.
