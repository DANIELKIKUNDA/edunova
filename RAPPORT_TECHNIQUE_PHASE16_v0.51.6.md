# EduNova v0.51.6 — Phase 16 / Inscriptions aux événements universitaires

## Continuité canonique et périmètre

**Parent :** `EduNova_v0.51.5_RC_PHASE16_CAMPUS_MAINTENANCE_LIFECYCLE.zip` (SHA-256 annoncé : `30c77fb419b84671ecd9579d8fef5b62d4058a9579e78fa6e9de127704197ccc`). Le paquet source a été extrait et son intégrité ZIP inspectée avant toute modification.

**Domaine :** Événements et vie de campus. Au lieu de créer un calendrier parallèle, cette version réutilise explicitement les événements `kind=event` du contexte déjà existant `campus_operations`, et ajoute une couche d'inscription facultative dans `campus_services`.

**Ne sont pas modifiés :** programme académique et plannings, notes et jury, Phase 14/15, autres politiques Campus existantes.

## Fonctionnalités livrées

- Paramétrage du **nombre de places** pour un événement par un gestionnaire autorisé (0 = inscriptions désactivées, 1 à 5000 = capacité déclarée), avec verrouillage du parent et version optimiste.
- Les anciens événements conservent `registration_capacity=0` par défaut : aucune inscription rétroactive implicite.
- Inscription personnelle d'un membre actif à un événement futur, publié comme `scheduled` et effectivement visible par ce membre via le **calendrier académique existant**.
- Calcul des places occupées et refus de dépassement, y compris après tentative de réduction de capacité. Le SQL PostgreSQL acquiert un verrou `SELECT ... FOR UPDATE` sur la ligne de l'événement avant le décompte et la mutation.
- Une seule inscription par couple `(event_id, account_id)` au niveau base ; double clic / rejeu refusé ; annulation versionnée et réinscription conservant l'historique.
- Visibilité personnelle des inscriptions, contrôle du rattachement à la cohorte pour les étudiants, isolation interuniversités, refus des rôles auditeurs en écriture, annulation possible après changement de cohorte ou annulation d'événement.
- API FastAPI, service métier, repository SQLAlchemy, migration **0092**, intégration Flutter (écran événements, création par administrateurs, gestion de places, inscription et désinscription), tests backend adversariaux et contrats de gateway Dart.

## Intégrité et sécurité

- Toujours utiliser `account_id` fourni par l'authentification, jamais un identifiant de participant soumis par le client.
- Refuser les événements d'autres institutions avant toute réponse sur leur existence ou la composition des inscriptions.
- Sérialiser les mutations capacité/inscription/désinscription en verrouillant la ligne du calendrier correspondante dans une transaction PostgreSQL ; l'unicité `(event_id, account_id)` défend en base les doublons.
- Éviter les lectures obsolètes côté Flutter : compteur de génération, effacement de l'état à chaque changement d'université ou de cycle de vie, nouveaux appels après reprise de l'application, cache institutionnel désactivé.
- Rejeter explicitement les entiers booléens envoyés pour `capacity` et `expected_version` par le contrat HTTP Pydantic `StrictInt`.
- Aucun recalcul de note officielle ; aucune écriture d'identité d'autrui ; aucune fonctionnalité de courriel/push/SMS annoncée.

## Limites connues

1. **Flutter/Dart :** SDK absent de cet environnement : les tests Flutter sont ajoutés aux sources mais ni `flutter analyze`, ni `flutter test`, ni la compilation ne sont déclarés exécutés.
2. **PostgreSQL réel :** le verrouillage et les indexes sont codés mais non certifiés sur un serveur PostgreSQL avec vraies transactions concurrentes. SQLite valide les opérations séquentielles et les contraintes locales, pas les garanties de concurrence PostgreSQL.
3. **Communication externe :** aucune notification SMS, courriel ou push lors de l'inscription ou annulation ; les services existants de notification ne sont pas réimplémentés.
4. **Contenu du reste de la Phase 16 :** activités Alumni, réservation coordonnée avec les emplois du temps, notifications et rappels Campus restent ouvertes.
5. Les Phases 14 et 15 gardent leur réserve de certification Flutter ; la Phase 17 n'est pas commencée.

## Fichiers clés

- `services/api/app/modules/campus_services/application/event_registration_service.py`
- `services/api/app/modules/campus_services/infrastructure/event_registration_repo.py`
- `services/api/app/modules/campus_services/api/router.py`
- `services/api/app/modules/campus_operations/infrastructure/sqlalchemy_repo.py`
- `services/api/migrations/0092_campus_event_registrations_v0_51_6.sql`
- `services/api/tests/test_phase16_event_registration_v0_51_6.py`
- `apps/mobile/lib/src/features/campus_services/infrastructure/campus_services_gateway.dart`
- `apps/mobile/lib/src/features/campus_services/presentation/campus_events_page.dart`
- `apps/mobile/lib/src/features/campus_services/presentation/campus_services_page.dart`
- `apps/mobile/lib/src/app/router.dart`
- `apps/mobile/test/campus_events_gateway_test.dart`

## Vérification

Les résultats exacts (code retour et total exécuté, pas estimé) figurent dans `REGRESSION_BACKEND_v0.51.6.txt`, `PREUVES_TESTS_v0.51.6.txt` et `STATIC_AUDIT_PHASE16_v0.51.6.txt`. La commande utilisée est :

```bash
PYTHONPATH=services/api python -m pytest -q services/api/tests
```

Les validations hors environnement (Flutter, PostgreSQL, Redis, stockage objet, fournisseurs et appareils réels) ne sont pas revendiquées.

**Décision :** nouveau checkpoint de développement de la Phase 16, pas clôture fonctionnelle de la Phase 16.

## Résultats définitifs de cette exécution

| Contrôle | Résultat |
|---|---|
| SHA-256 de l'archive parente | Vérifié, correspond au checkpoint v0.51.5 |
| Régression backend **après** les changements | **1030/1030 PASS** (205,37 s, code retour 0) |
| Tests ciblés incluant migration | **20/20 PASS** (6,29 s) |
| Nouveaux tests backend | **19**, en plus des 1011 tests précédents |
| Compilation syntaxique Python | PASS |
| Audit structurel (non équivalent Dart/Flutter) | **12/12 PASS** |
| Flutter analyze/test/build | NON EXÉCUTÉS |
| PostgreSQL/Redis/stockage objet réels | NON EXÉCUTÉS |

Cette certification est **locale backend et structurelle frontend**. Elle ne représente ni une certification Flutter, ni une validation appareil physique, ni une homologation infrastructure de production.
