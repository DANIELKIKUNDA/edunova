# EduNova v0.50.9 — checkpoint canonique

## Source et décision

Source intégrale : `EduNova_v0.50.8_RC_PHASE14_15_FLUTTER_BRIDGE.zip`.
Roadmap v1.0 inchangée. Phases 0–13 conservées ; Phases 14/15 backend local déjà clôturé ; Phase 16 non entamée.

**Nouvelle règle d'acceptation demandée :** clôture fonctionnelle = backend ET frontend développés, intégrés et **vérifiés**. Les validations sur appareils sont réservées à la Phase 23. L'absence de Flutter SDK sur cet environnement interdit de certifier ici la compilation et les tests Dart.

## Corrections et fonctionnalités livrées dans le code

- Phase 14 : objectif pédagogique et preuve de provenance visibles ; gestion authentifiée du référentiel d'objectifs, association question–objectif, rattachement de blueprint existant ; rafraîchissement depuis la réponse canonique serveur après écriture ; aucune modification des notes ou du jury.
- Phase 15 : archives gouvernées, consultation de l'historique, capture immuable avec confirmation explicite, comparaison historique lorsqu'autorisée et aperçu CSV volatile limité à 256 KiB ; aucun fichier sensible stocké par ces nouveaux écrans.
- Confidentialité : seuls les indicateurs libérés par le backend sont affichés ; archives masquées non ouvertes ; avertissements sur limites de provenance et comparaison ; données d'une institution tierce rejetées à la sélection d'entrée.
- RBAC : accès effectif de l'auditeur à la vue institutionnelle en lecture seule ; interdiction de capture pour le rôle AUDITOR côté serveur ; correction **backend** du contrôle `FACULTY_ADMIN` en Phase 14 : seuls les cours figurant dans le périmètre des facultés autorisées sont consultables/modifiables. Tests adversariaux correspondants.
- CI Flutter ajouté : `flutter pub get`, `flutter analyze --no-pub` et `flutter test --no-pub` sur *l'ensemble* des tests Flutter de l'application mobile à exécuter dans une machine possédant Flutter. Ne pas confondre définition de CI et exécution de CI.

## Preuves locales réelles

- Régression backend après toutes modifications backend : **900/900 PASSED**, exit 0 (169.76 s). Entrée : `PYTHONPATH=services/api python -m pytest -q services/api/tests`.
- Ciblé contrat Phase 14/15 frontend : **6/6 PASSED**.
- Ciblé Phase 14 + correction RBAC faculté : **98/98 PASSED**.
- Ciblé RBAC auditeur et captures : **2/2 PASSED**.
- `compileall` backend/tests : PASS.
- Audit structurel LOT30 : **23/23 PASS**.
- Inspection statique limitée de l'intégration Dart : **23/23 PASS** (ce n'est PAS `flutter analyze`).
- Vérification syntaxique shell et parsing YAML CI : PASS.

## Validations non exécutées et réserves

- `flutter pub get`, `flutter analyze`, `flutter test`, compilation native : **NON EXÉCUTÉS** (SDK Flutter/Dart absent).
- Les nouveaux tests Dart ont été écrits, mais ne sont pas attestés PASS.
- Vérification visuelle responsive/accessibilité et certification sur appareil : NON EXÉCUTÉES.
- PostgreSQL/Redis et object storage réels, concurrents à grande échelle : NON EXÉCUTÉS dans cette itération.
- Les restrictions de confidentialité des comparaisons statistiques ne prouvent pas une anonymisation universelle.

**Décision de clôture :** intégration de code Phase 14/15 substantiellement consolidée ; backend local vérifié. Selon la règle de clôture intégrale choisie, Phases 14/15 restent **en attente de certification Flutter**. Ne pas déclarer une clôture fonctionnelle intégrale ni lancer la Phase 16 avant réussite et traitement des éventuels défauts de `flutter analyze`/`flutter test`.
