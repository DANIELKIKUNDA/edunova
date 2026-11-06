# EduNova v0.53.3 — Phase 18 : vérification Campus par université dans Flutter

- Provider Riverpod `campusCombinedAccessProvider` paramétré par identifiant institutionnel, `autoDispose` et appel API authentifié.
- Chaque affiliation active affiche un état commercial Campus vérifié par l'API existante, sans déduire la licence de la seule affiliation.
- En cas d'erreur réseau : statut **non vérifié**, réessai possible, jamais de droit Campus affirmé.
- Les droits Premium personnels demeurent indépendants de la licence Campus.
- Les autorisations d'accès aux ressources demeurent exclusivement appliquées par le backend.
- Tests Phase 18 : 21 réussis (`PYTHONPATH=services/api python -m pytest -q services/api/tests/test_phase18*`).
- Flutter SDK absent : compilation Flutter et tests Dart non exécutés. Pas de régression backend globale dans ce lot.
- À poursuivre : renouvellements, expiration, offres et contrôle de capacité institutionnelle; certification appareil réel différée.
