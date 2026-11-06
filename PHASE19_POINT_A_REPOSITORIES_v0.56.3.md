# EduNova v0.56.3 — Phase 19, point A — protection des repositories

## Périmètre réalisé

Ajout du contrôle `LocalAccountAccess` aux repositories Drift suivants : assistant (conversations/messages), plans d'études, planification adaptative, pédagogie (résumés, progression, erreurs) et espace de travail documentaire. Les opérations asynchrones couvertes vérifient l'accès avant leur exécution et les flux Drift couverts revérifient l'accès avant chaque émission via `protect`.

Le repository des documents personnels était déjà protégé dans v0.56.2.

## Vérifications

- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync_lot7.py` : **17 passed**, 11.14 s.
- SDK Flutter/Dart absent : **analyse Dart, compilation et tests Flutter non exécutés**.
- Les tests backend ne valident pas les nouvelles protections Dart.

## Limites et risques ouverts

- Les autres repositories locaux (bibliothèque, profil académique, analytics, audio, engagement, commerce, livraison, synchronisation, etc.) nécessitent une revue dédiée pour déterminer quelles opérations exposent des données privées et quelles opérations doivent fonctionner anonymement.
- Le modèle de propriété unique n'est pas un cloisonnement physique de la base SQLite par compte.
- Le contrôle d'accès avant une opération asynchrone ne garantit pas, à lui seul, une révocation atomique en cas de déconnexion concurrente pendant l'opération.
- `LocalAccountAccess` autorise les installations sans propriétaire ; la garantie de non-réattribution dépend du bootstrap et des contrôles d'installation historiques.

**Décision : point A non certifié.** Ne pas passer au point B avant audit du périmètre restant et tests Flutter.
