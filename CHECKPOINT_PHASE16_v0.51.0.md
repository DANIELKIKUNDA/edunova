# EduNova v0.51.0 — Phase 16 / Campus Services Foundation

**Base canonique :** `EduNova_v0.50.10_RC_PHASE14_15_FLUTTER_SECURITY_DEEPENING.zip`.
**Roadmap :** identique, phases 0 à 15 préservées. **Phase 16 : EN COURS**, cette livraison **n'en est pas la clôture**.

## Inspection du code existant avant intervention

- `campus` : institutions, memberships, rôles, unités, cohortes.
- `campus_operations` : présences, annonces et calendrier opérationnel ; **réutilisés**, non recodés.
- `teaching` : cours, offres de cours, sessions ; conservé.
- `library` : catalogue de **contenus pédagogiques numériques**, ce n'est pas un logiciel d'emprunt physique.
- Flutter `CampusPage`, `CampusIntelligenceGateway` et routeur `go_router` : réutilisés.
- Recherche des fonctionnalités physiques : aucun contrat serveur autonome de réservation de salles/laboratoires/équipements n'était présent dans les modules inspectés.

## Développement réel effectué

**Périmètre choisi : ressources physiques et réservation** (un premier domaine des services Campus).

1. `campus_services` : modèle `CampusResource`, `CampusBooking`, types salle, laboratoire, équipement, espace bibliothèque.
2. API FastAPI institutionnelle : lister/créer/désactiver des ressources, lister/créer/annuler des réservations (`/v1/campus-services/institutions/{institution_id}/...`).
3. RBAC au backend : seuls owner/rector/admin/academic_admin créent et désactivent ; auditeur lecture seule ; membre actif uniquement ; accès inter-universités interdit.
4. Réservations : délais limités (90 jours), maximum huit heures, fuseau explicite, chevauchements interdits par intervalle demi-ouvert `[début, fin)`.
5. PostgreSQL : sérialisation applicative des modifications par verrou transactionnel `SELECT ... FOR UPDATE` sur la ligne ressource ; annulation et désactivation par mises à jour optimistes `row_version`.
6. Visibilité : membres ordinaires et administrateurs de faculté ne lisent que leurs propres réservations ; administrateurs globaux et auditeurs peuvent voir celles de leur institution. Les filtres sont appliqués dans la requête **avant** pagination.
7. Migration `0086_campus_physical_resources_v0_51_0.sql` : deux tables, index, contraintes et FK. Le contrat de couverture des migrations existant a été actualisé, sans suppression des entrées antérieures.
8. Flutter : `CampusServicesGateway` authentifié, écran `CampusServicesPage` (liste, création de ressource, réservation, annulation), navigation depuis `CampusPage`, effacement des états au changement de tenant/application suspendue.
9. Tests : 12 nouveaux tests backend, cas adversariaux RBAC, frontières tenant, conflit temporel, format des heures, annulations obsolètes, doublons, institutions suspendues. Deux tests Flutter du gateway **écrits mais non exécutés**.

## Vérification réellement exécutée

- Checkpoint source : **900/900** tests backend réussis avant développement.
- Régression intermédiaire : **911 PASS / 1 FAIL** ; échec dû à la liste canonique des migrations non encore actualisée pour `0086`. Le test a été corrigé pour inclure la migration et charger ses modèles, **sans relâcher le contrôle d'exhaustivité des tables**.
- Vérification ciblée corrigée : **13/13 PASS** (migration + 12 nouveaux tests).
- **Régression globale finale : 912/912 PASS**, sortie 0, durée **83,80 s**.
- Compilation syntaxique Python : **PASS** via `python -m compileall`.
- Archive ZIP et SHA-256 : voir preuves séparées.
- **Flutter analyze, flutter test, flutter build : NON EXÉCUTÉS** (SDK absent de l'environnement).
- **Migration sur PostgreSQL réel et concurrence multi-processus : NON EXÉCUTÉES**, à valider avec une base réelle. SQLite ignore `FOR UPDATE` ; les tests SQLite démontrent les comportements séquentiels, pas la sérialisation PostgreSQL.
- Redis, stockage objet et appareils physiques : non testés ici.

## Travaux restants en Phase 16 (non déclarés finis)

- Bibliothèque **physique** : exemplaires, prêts, retours, pénalités selon politique institutionnelle ; le catalogue numérique existant ne doit pas être reconstruit.
- Inventaire/maintenance avancés des équipements et bâtiments.
- Coordination obligatoire avec les séances académiques et calendriers existants : empêcher qu'une réservation bloque une salle déjà affectée à un cours. Le moteur de réservation autonome livré ici ne dispose pas encore de cette intégration.
- Vie universitaire/événements : étendre les annonces/calendrier existants uniquement après inspection des besoins, sans duplication.
- Alumni : identifier le contrat et le périmètre métier, développer backend + Flutter si non existants.
- Prise en charge évolutive : pagination bornée actuelle à 250, filtrage des recherches et tests de charge à compléter.
- Flutter : sur machine équipée du SDK, lancer `flutter pub get`, `flutter analyze`, `flutter test`, `flutter build` (selon cible), puis corriger les anomalies éventuelles. Certification appareils réels reste en Phase 23.

## Statut des Phases 14 et 15

Backend local conservé, mais **clôture fonctionnelle intégrale en attente de vérification Flutter** conformément à la règle décidée avec l'utilisateur. La Phase 19 reste dédiée à la consolidation mobile/offline/UX, et la Phase 23 à la certification sur appareils réels.
