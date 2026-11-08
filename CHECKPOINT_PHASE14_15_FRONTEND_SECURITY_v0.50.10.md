# Checkpoint canonique EduNova v0.50.10

**Origine :** v0.50.9, ZIP intégral contrôlé par SHA-256.

**Chantier :** consolidation frontend Flutter des Phases 14 (Intelligence pédagogique) et 15 (Intelligence institutionnelle), isolation multi-universités lors de la navigation, races A-B-A, sécurité des droits révoqués, archivage CSV volatile et reprise du cycle de vie mobile.

**Vérifications backend locales :** 900/900 PASS ; 11/11 PASS ciblés ; audit structurel 23/23 ; contrôle statique Flutter non compilant 33/33 ; syntaxe Python et shell, YAML CI PASS.

**SDK Flutter/Dart absent :** pas de compilation Dart, pas de `flutter analyze`, pas de `flutter test`. Nouveaux tests Flutter écrits mais non exécutés.

**État :** backend 14/15 localement clôturé ; frontend 14/15 code approfondi, non certifié ; phase 16 non commencée ; phases 0-13 conservées. Dernière migration : 0085.

**À faire sur un environnement équipé Flutter :** `bash scripts/certify_phase14_15_flutter.sh`, corriger tous les défauts signalés par le compilateur/analyseur et les tests, puis enregistrer leurs journaux dans un nouveau checkpoint. Validation appareil réel à la Phase 23.

Rapport détaillé : `RAPPORT_TECHNIQUE_PHASE14_15_FRONTEND_v0.50.10.md`.
