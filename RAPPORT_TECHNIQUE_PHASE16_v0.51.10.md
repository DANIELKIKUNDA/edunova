# EduNova v0.51.10 — Phase 16 : sécurité des liens Alumni

Base canonique : v0.51.9.

## Modification effective
- Validation renforcée des liens HTTPS des opportunités Alumni : refus des adresses IP littérales, destinations locales, credentials, ports invalides, fragments et caractères de contrôle.
- Dix tests adversariaux ajoutés.

## Preuves exécutées
- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_phase16_academic_alumni_v0_51_8.py services/api/tests/test_phase16_closure_v0_51_9.py` : **30 PASS** en 9,50 s.
- Régression backend complète : lancement effectué, résultat final non confirmé au moment de ce paquet.
- Flutter SDK : absent de l'environnement, `flutter pub get`, `flutter analyze`, tests et builds non exécutés.

## Statut
Phase 16 non certifiée entièrement. Aucun PASS Flutter ou régression complète n'est revendiqué sans preuve.
