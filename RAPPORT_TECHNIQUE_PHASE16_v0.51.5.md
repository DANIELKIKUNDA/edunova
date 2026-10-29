# EduNova v0.51.5 — Phase 16 / Campus Maintenance Lifecycle

**Source canonique :** v0.51.4 (SHA-256 `6b068d4bbeefb8afcd2a46086b8706d902948c96109ebe716da25f0e56f206ea`), entièrement réutilisée sans reconstruction.

**Portée :** développement réel du cycle de maintenance des salles, laboratoires, équipements et espaces Campus, backend + interface Flutter. La Phase 16 reste ouverte.

## Implémentation
- Nouveau contrat SQL versionné **0091** : état opérationnel sur les ressources, raison d'annulation des réservations, table de tickets et index partiel interdisant plus d'un ticket ouvert par ressource.
- Cycle métier **reported → in_progress → resolved** ou **reported → dismissed**. Le signalement non validé ne suspend pas les réservations ; seul un administrateur autorisé peut immobiliser, clôturer ou rejeter.
- Lors de l'immobilisation, verrouillage transactionnel de la ressource et annulation atomique des réservations non terminées (`ends_at > now`), avec `cancellation_reason=resource_maintenance`, incrément des versions et conservation historique. La remise en service ne réactive pas les réservations annulées.
- Intégrité : contrôle de version des tickets, disponibilité vérifiée dans la même transaction que la réservation, gestion des doublons, refus des mutations hors université et contrôle des membres actifs.
- RBAC : auditeurs en lecture seule ; étudiants, enseignants et membres habilités peuvent signaler ; seuls OWNER/RECTOR/ADMIN/ACADEMIC_ADMIN peuvent démarrer ou clôturer. Les utilisateurs ordinaires ne consultent que leurs propres tickets.
- Flutter : signalement, tableau des tickets, décisions administrateur avec confirmation, statut de disponibilité et motif des réservations annulées, protection contre la réutilisation de données en cas de changement d'université et rétention locale interdite.
- Ajout de tests backend adversariaux (transactions, rôles, tenants, versions, API réelle) et deux tests Dart de contrat gateway (non exécutés localement).

## Résultats vérifiés localement
- **Python / backend : 1011/1011 tests PASS**, code de sortie 0, fichier `REGRESSION_BACKEND_v0.51.5.txt`.
- **Tests backend ciblés : 37/37 PASS**, incluant tests préexistants et nouveau module.
- **Audit structurel Phase 16 : 21/21 PASS** ; contrôle statique préexistant Phases 14/15 : **33/33 PASS**.
- `python -m compileall -q services/api/app` : terminé sans erreur.
- Contrat des migrations : PASS et migration 0091 ajoutée sans suppression.
- Intégrité du ZIP et du manifeste : contrôle après fabrication de l'archive.

## Réserves explicites — aucune extrapolation
- **Flutter** : SDK `flutter`/`dart` absent ; `flutter analyze`, `flutter test`, compilation et rendu UI **non exécutés**. Les tests Dart sont écrits mais leur réussite n'est pas revendiquée. CI existante exécute `flutter analyze` et `flutter test` lorsque l'agent Flutter est disponible.
- **Infrastructure** : PostgreSQL réel, Redis, workers, stockage objet et appareils physiques **non certifiés** ; les cas transactionnels ont été vérifiés avec SQLite et le protocole PostgreSQL reste à valider en environnement réel.
- **Notifications** : les réservations sont annulées en base avec motif visible dans le compte, **sans envoi push/email/SMS** dans cette version.
- **Autres services Phase 16** : événements, alumni, maintenance préventive, notifications de bibliothèque, politique planning-réservations demeurent à approfondir. Ne pas confondre ce checkpoint avec la clôture de la Phase 16.

## Exécution des tests
```bash
PYTHONPATH=services/api python -m pytest -q services/api/tests
```
La première exécution globale de cette itération a dépassé le timeout du terminal ; elle a été relancée en processus détaché, son fichier de sortie et son code de retour ont été vérifiés jusqu'à terminaison. Le résultat final **1011 PASS** est issu de cette exécution détachée terminée.
