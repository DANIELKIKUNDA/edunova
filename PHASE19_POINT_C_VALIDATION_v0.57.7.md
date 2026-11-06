# EduNova — Phase 19, point C : validation technique (v0.57.7)

Date : 23 octobre 2026. Base : archive complète v0.57.6.

## Contrôles effectivement exécutés

- Extraction de l'archive v0.57.6 : réussie.
- Compilation syntaxique Python : `python -m compileall -q services/api` : réussie.
- Tests backend de synchronisation : `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync*` : **17 réussis**, en 9,55 s.
- Régression backend complète : lancée avec `PYTHONPATH=services/api python -m pytest -q services/api/tests` ; **interrompue par la limite de temps de 200 secondes**, après progression affichée à 6 %. Résultat global indéterminé ; aucun succès global revendiqué.
- SDK Flutter/Dart : commandes `flutter` et `dart` introuvables. **Aucune compilation Flutter ni test Dart exécuté**.

## Réserve de sécurité constatée à l'inspection

Dans `apps/mobile/lib/src/core/security/local_account_access.dart`, `assertReadable()` autorise les lectures lorsque `ownerAccountId()` est nul. Le commentaire suppose une installation anonyme propre, mais cette méthode ne vérifie pas elle-même l'absence de données héritées. Le point A ne peut donc pas être déclaré formellement certifié pour les accès directs qui utilisent `assertReadable()`.

`sessionRevision` est un compteur en mémoire de processus : il ne prouve pas une annulation universelle des opérations en arrière-plan ou inter-isolates.

## Décision

**Phase 19 : non certifiée à ce stade.** Les points A et B sont consolidés au niveau du code, mais les réserves ci-dessus, les tests Flutter et la régression backend globale empêchent une certification complète. Les essais sur appareils réels restent prévus en phase 23 ; ils ne remplacent pas la compilation et les tests Flutter nécessaires ici.

## Suite ciblée (sans multiplication de checkpoints)

1. Installer ou rendre disponible Flutter/Dart, lancer `flutter analyze` et `flutter test` dans `apps/mobile`, puis corriger les erreurs réelles.
2. Exécuter la régression backend complète avec une durée suffisante ; archiver le bilan chiffré.
3. Corriger/justifier la politique `owner == null` pour tous les repositories privés, avec tests de non-divulgation et de déconnexion concurrente.
4. Reprendre la décision de clôture de la phase 19 uniquement sur preuves.
