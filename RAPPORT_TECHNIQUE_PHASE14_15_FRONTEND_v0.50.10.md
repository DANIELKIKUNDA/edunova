# EduNova v0.50.10 — rapport technique Phase 14/15

## Source canonique et périmètre

Source **vérifiée** : `EduNova_v0.50.9_RC_PHASE14_15_FRONTEND_CONSOLIDATION_FINAL.zip` ; SHA-256 de la source : `8642c7b2ca9570cdabb9b88f404cabd2f00c989086c08f1ed308afcb0137184e`.
Périmètre : correction et consolidation **frontend Flutter** des Phases 14 et 15, sans refonte de modules préexistants, sans nouvelle migration SQL (dernière : 0085), sans intervention sur les notes/jury. Roadmap inchangée, Phase 16 non entamée.

## Défauts concrets traités

1. **Réutilisation du State lors d'un changement d'université** : `InstitutionIntelligencePage.didUpdateWidget` revalide désormais la nouvelle institution et efface les anciennes sélections/agrégats avant tout chargement. L'ancien code ne gérait pas ce cas lors d'une navigation qui réutilise l'élément Flutter.
2. **Course/period A → B → A et appels asynchrones périmés** : des compteurs de génération par flux (enseignant, direction, comparaison) empêchent qu'une ancienne réponse concernant les mêmes identifiants remplace une réponse plus récente.
3. **Révocation/expiration de session (HTTP 401/403)** : les agrégats institutionnels affichés sont supprimés immédiatement lors d'un refus des API ; l'échec de rapprochement gradebook 401/403 n'est plus absorbé comme simple indisponibilité facultative.
4. **Doublons et références institutionnelles malformées** : les listes de cours et de périodes rejetées avant création de menus ambigus (validation des identifiants, unicité stricte).
5. **Archives/statistiques à périmètre modifié** : le changement d'université, de période, d'unité ou de droit de capture invalide tous les résultats en cours, y compris le CSV volatil et les confirmations avant POST. L'action de capture vérifie la génération ET l'autorisation lors du retour de la boîte de confirmation.
6. **Aperçu CSV** : le dialogue flottant (susceptible de survivre à un changement de périmètre) a été remplacé par un aperçu **inline** non sélectionnable, à durée de vie limitée au widget. Pas d'écriture locale ; borne mémoire et validation `text/csv` existantes conservées.
7. **Mise en arrière-plan** : les panneaux effacent leurs agrégats/aperçus et invalident les réponses en vol ; au retour au premier plan, les accès sont revérifiés par le serveur. Cette précaution réduit le risque d'exposition visuelle, sans prétendre certifier les captures d'écran de l'OS.
8. **Formulaires d'objectifs** : une sélection de cours obsolète et une mutation abandonnée ne laissent plus le panneau bloqué en état d'enregistrement ; les rafraîchissements pendant une mutation sont désactivés.

## Fichiers de code modifiés

- `apps/mobile/lib/src/features/campus_intelligence/presentation/institution_intelligence_page.dart`
- `apps/mobile/lib/src/features/campus_intelligence/presentation/institutional_archive_panel.dart`
- `apps/mobile/lib/src/features/campus_intelligence/presentation/pedagogical_governance_panel.dart`
- `apps/mobile/pubspec.yaml` (numéro de version)
- `scripts/audit_campus_intelligence_flutter.py` (33 contrôles statiques)
- `scripts/certify_phase14_15_flutter.sh` (tests ciblés + suite intégrale)
- `.github/workflows/ci.yml` (job Flutter : tests adversariaux ciblés puis suite générale)

## Tests Flutter ajoutés mais NON exécutés

- `apps/mobile/test/campus_intelligence_tenant_transition_widget_test.dart` : changement d'université pendant requête, course A→B→A, références de cours dupliquées, révocation HTTP 403 avec suppression de la vue précédente.
- `apps/mobile/test/campus_intelligence_archive_scope_widget_test.dart` : ancienne réponse CSV après changement de période, effacement au passage en arrière-plan, révocation du droit de capture pendant la confirmation.

**Ces 7 scénarios Flutter sont des tests écrits et intégrés à la CI, pas des tests réussis.** La machine locale ne possède ni `flutter` ni `dart`, comme attesté par `evidence/FLUTTER_AVAILABILITY_v0.50.10.txt`. `flutter pub get`, `flutter analyze`, `flutter test` et les compilations mobile **n'ont pas été exécutés**. Les 33 vérifications Python sont uniquement un audit statique de contrats, pas une validation du compilateur Dart.

## Vérifications effectivement exécutées

- Backend : `PYTHONPATH=services/api python -m pytest -q services/api/tests` → **900/900 PASS**, exit 0, 141,55 secondes (journal intégral : `evidence/FINAL_BACKEND_REGRESSION_v0.50.10.txt`). Backend inchangé, régression de non-régression.
- Contrats API et RBAC ciblés → **11/11 PASS** (`evidence/TARGETED_AUTH_ROUTES_v0.50.10.txt`).
- `python -m compileall -q services/api/app scripts` → **PASS** (syntaxe Python uniquement).
- `python scripts/audit_lot30.py` → **23/23 PASS** (`evidence/STRUCTURAL_AUDIT_v0.50.10.txt`).
- `python scripts/audit_campus_intelligence_flutter.py` → **33/33 PASS** (`evidence/STATIC_AUDIT_PHASE14_15_v0.50.10.txt`).
- `bash -n scripts/certify_phase14_15_flutter.sh` et parsing YAML de la CI → **PASS**.
- Archive et empreintes SHA-256 → vérifiées au conditionnement, voir le fichier SHA-256 externe.

## Réserves et décision

- Les contrôles RBAC des services existants continuent de s'appliquer côté FastAPI, et les données sensibles ne sont pas conservées dans une base offline par les nouveaux panneaux.
- Tests PostgreSQL/Redis/object-storage réels et tests sur appareils **non exécutés** ; ces certifications restent planifiées aux phases prévues.
- Les mécanismes de confidentialité des consultations statistiques atténuent certains risques, mais ne prouvent pas une anonymisation universelle.
- **Clôture backend locale des Phases 14 et 15 conservée** (suite de 900 PASS). **Clôture fonctionnelle complète non prononcée** en l'absence de validation Flutter/Dart. Phases 14/15 : frontend approfondi et soumis à des tests écrits, certification Flutter en attente. Phase 16 : non entamée.
