# EduNova v0.54.3 — Phase 19 / validation des lots entrants

## Implémentation
- Flutter `RunCloudSync`: validation intégrale du bootstrap avant toute écriture locale (curseur, plancher de rétention, version et séquence des enregistrements).
- Validation des lots delta avant écriture locale : aucun enregistrement hors de l'intervalle `(cursor, nextCursor]`, version positive, bornes de rétention cohérentes.
- Vérification de l'accusé de réception serveur : rejet d'un accusé négatif, supérieur au curseur téléchargé ou inférieur à l'accusé précédent.
- Deux scénarios Flutter ajoutés pour les lots malformés, avec assertions d'absence d'application locale.

## Vérification
- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync_lot7.py` : **17 passed**.
- Tests Flutter **non exécutés** (SDK Flutter absent).
- Régression générale non exécutée.

## Limites
La Phase 19 n'est pas certifiée. Ces protections ciblent les incohérences du protocole, et ne remplacent ni les transactions de stockage local, ni les tests sur appareils.
