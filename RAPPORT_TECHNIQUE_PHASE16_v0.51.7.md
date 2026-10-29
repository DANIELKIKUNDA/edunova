# Rapport technique — EduNova v0.51.7

**Phase 16 : Centre d'alertes Campus personnelles, consultation en ligne**  
**Point de reprise :** EduNova v0.51.6 (SHA-256 vérifié : `2a0017b63f668d4bad4a49e84918e90f4a0d14fcbdd80c3c639443593567d3fb`).  
**Statut :** livraison fonctionnelle backend locale, frontend Flutter intégré au code et non compilé. **Phase 16 non clôturée.**

## Inspection du code et choix d'intégration

Le checkpoint précédent disposait déjà de la bibliothèque physique, des réservations, de la maintenance des ressources et des inscriptions aux événements rattachés au calendrier institutionnel. L'application possède un écran Flutter `CampusServicesPage`, une gateway Dio authentifiée, ainsi qu'un service d'engagement avec préférences de notification. La présente version n'a reconstruit aucun de ces modules ni lancé de canal SMS/email/push. Elle ajoute une **consultation personnelle à la demande**, dérivée des données métier existantes.

## Fonctionnalités ajoutées

- **Échéances de bibliothèque** dans les trois prochains jours et **retards** encore ouverts.
- **Réservations annulées pour maintenance**, pour le compte authentifié et dans une période pertinente (fin de réservation au maximum 7 jours avant maintenant).
- **Événements imminents** (démarrant dans les prochaines 24 h) et **événements annulés**, uniquement si l'inscription personnelle demeure active.
- Actualisation à l'ouverture / retour sur l'écran et par bouton manuel ; un retour d'emprunt ou une désinscription modifie immédiatement le résultat à la consultation suivante.
- API `GET /v1/campus-services/institutions/{institution_id}/alerts`, adossée à `runtime.campus_alerts`.
- Interface Flutter « Mes alertes Campus », dans l'écran existant des services du campus, avec messages français et niveaux `urgent`, `warning`, `info`.

## Défense en profondeur

1. L'identifiant du compte provient **exclusivement** du contexte authentifié HTTP ; il n'existe aucun paramètre `account_id` fourni par le client.
2. Le service vérifie une appartenance **ACTIVE** dans une université **ACTIVE** avant la consultation.
3. Toutes les sources SQL sont filtrées sur **institution_id ET compte concerné**, y compris pour les comptes propriétaires, administrateurs ou auditeurs ; aucun tableau global n'est retourné.
4. Les messages ne contiennent ni nom d'emprunteur, ni détail du livre, ni nom de participant. Les références exposées identifient seulement l'objet personnel à l'origine de l'alerte.
5. La réponse est bornée à 50 alertes et les lectures de chaque source sont bornées à 100 enregistrements. Des histoires très volumineuses peuvent être partiellement représentées : cette fonctionnalité n'est pas un journal exhaustif.
6. L'interface efface les données lors d'un changement d'université, d'un passage en arrière-plan et d'une erreur ; les réponses réseau périmées sont rejetées grâce au compteur de génération existant. La gateway vérifie les identifiants dupliqués et les niveaux autorisés.
7. L'API n'a aucun effet sur les prêts, les notes, le jury ou les réservations : aucune écriture et aucun acquittement de notification.

## Fichiers ajoutés ou modifiés

- `services/api/app/modules/campus_services/infrastructure/campus_alerts_repo.py` — projection SQL personnelle.
- `services/api/app/modules/campus_services/application/campus_alerts_service.py` — contrat de priorité et fenêtres temporelles.
- `services/api/app/modules/campus_services/api/router.py` — route FastAPI authentifiée.
- `services/api/app/runtime.py` — injection de dépendances dans le runtime existant.
- `services/api/tests/test_phase16_campus_alerts_v0_51_7.py` — tests SQL/HTTP positifs et adversariaux.
- `apps/mobile/lib/src/features/campus_services/infrastructure/campus_services_gateway.dart` — requête authentifiée `no-store` et validation JSON.
- `apps/mobile/lib/src/features/campus_services/presentation/campus_services_page.dart` — affichage utilisateur et nettoyage du cycle de vie.
- `apps/mobile/test/campus_alerts_gateway_test.dart` — contrat Flutter **écrit mais non exécuté**.

**Migration SQL :** aucune. Les données sont des projections en lecture des tables existantes ; dernière migration conservée **0092**.

## Résultats de vérification observés

| Vérification | Résultat |
|---|---|
| SHA-256 de l'archive v0.51.6 parente | Correspondance vérifiée |
| Tests nouveaux ciblés | **12/12 PASS**, 4,98 s |
| Régression backend globale **après modification** | **1042/1042 PASS**, 223,74 s, retour `0` |
| Compilation syntaxique Python | PASS, retour `0` |
| Inspections de raccordement API/Flutter | 6/6 présentes (inspection structurelle, **non** compilation Dart) |
| `flutter analyze`, `flutter test`, compilation APK | **NON EXÉCUTÉS** : SDK absent |
| PostgreSQL/Redis/stockage objet réels | **NON EXÉCUTÉS** |
| Tests sur appareils physiques | **NON EXÉCUTÉS** — Phase 23 |

Journaux : `REGRESSION_BACKEND_v0.51.7.txt`, `REGRESSION_BACKEND_v0.51.7.exit`, `TESTS_CIBLES_v0.51.7.txt`, `AUDIT_STRUCTURE_PHASE16_v0.51.7.txt`.

## Limites et suites

Cette interface est un **centre d'alertes à l'ouverture**, et non une notification distribuée ; il n'y a ni tâche de rappel en arrière-plan, ni SMS, ni mail, ni push. L'intelligence temporelle découle de l'état actuel de la base, sans historique d'acquittement.

Le chantier reste ouvert pour la coordination des salles/laboratoires avec les séances académiques, le périmètre Alumni, d'éventuelles notifications sortantes avec fournisseurs certifiés, et pour la validation Dart/Flutter. La certification de concurrence sur PostgreSQL réel n'a pas été revendiquée.

**Décision :** EduNova v0.51.7 devient le checkpoint canonique du développement de la Phase 16 ; ne pas déclarer la Phase 16 fonctionnellement clôturée.
