# Rapport technique de consolidation Phases 14–15 — v0.50.9

## Base et périmètre

Source contrôlée : v0.50.8 ; développement incrémental, zéro refonte, schéma SQL inchangé (dernière migration 0085). Le code n'écrase ni le gradebook ni les résultats publiés, ni les décisions du jury. `apps/admin` (administration éditeur Volcano Tech) n'est pas présumée être l'application destinée aux gestionnaires universitaires.

## Changements par fichier

| Composant | Développement |
|---|---|
| `apps/mobile/lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart` | ajout des routes authentifiées de gestion d'objectifs et d'archives, extraction CSV limitée en mémoire ; en-têtes no-store, validation d'ID ; aucune persistance locale |
| `apps/mobile/lib/src/features/campus_intelligence/presentation/pedagogical_governance_panel.dart` | nouveaux formulaires objectifs, associations de questions, liens d'évaluations, provenance des preuves et erreurs de permissions ; rechargement serveur après mutation |
| `apps/mobile/lib/src/features/campus_intelligence/presentation/institutional_archive_panel.dart` | historique avec suppression des contenus privés, création confirmée, comparaison gouvernée, aperçu CSV éphémère |
| `apps/mobile/lib/src/features/campus_intelligence/presentation/institution_intelligence_page.dart` | intégration des deux panneaux et sélection des périodes historiques, prise en compte du rôle d'auditeur, garde sur données supprimées, nettoyage d'état |
| `apps/mobile/lib/src/features/campus/presentation/campus_page.dart` | rôle `auditor` admis vers sa vue read-only |
| `services/api/app/modules/pedagogical_intelligence/application/service.py` | correctif P1 : limitation FACULTY_ADMIN aux offres renvoyées par `TeachingService.my_offerings` (filtrage hiérarchique préexistant) |
| `services/api/app/modules/institutional_analytics/application/service.py` | rôle AUDITOR limité aux lectures : archivage persistant refusé côté serveur |
| `services/api/tests/test_phase15_auditor_read_only_frontend.py` | 2 tests positif/adversarial lecture autorisée / capture interdite |
| `services/api/tests/test_phase14_faculty_scope_frontend_hardening.py` | 3 tests positifs/adversariaux du périmètre faculté |
| `services/api/tests/test_phase14_15_flutter_completion_contract.py` | 4 tests de contrats d'authentification et de méthodes HTTP pour les routes utilisées |
| `apps/mobile/test/campus_intelligence_governance_gateway_test.dart` | tests Dart écrits : auth, périmètres, POST, route injection, mode export |
| `apps/mobile/test/campus_intelligence_completion_widget_test.dart` | tests widget écrits : présentation pédagogique et non-exposition des données masquées |
| `.github/workflows/ci.yml` | nouveau job `campus-flutter` avec analyse/test global Flutter à exécuter en CI |
| `scripts/certify_phase14_15_flutter.sh` | procédure reproductible de certification Flutter |
| `scripts/audit_campus_intelligence_flutter.py` | tests statiques simples des points de liaison ; ne remplace pas le compilateur Dart |

## Validation et résultats

Tous les résultats mentionnés sont issus de journaux réellement produits durant cette itération ; voir `TEST_EVIDENCE_PHASE14_15_FRONTEND_v0.50.9.txt`, `FINAL_BACKEND_REGRESSION_v0.50.9.txt` et `STATIC_AUDIT_PHASE14_15_v0.50.9.txt`.

Backend : 900/900 PASS en 169.76 s. Ciblé contrat : 6/6 PASS ; Phase14+faculté : 98/98 PASS. Compilation syntaxique Python : PASS. Audit structurel : 23/23 PASS. Audit statique restreint frontend : 23/23 PASS.

**Ne pas compter les tests Flutter comme exécutés** : ni SDK Flutter ni Dart disponibles. La CI Flutter est une procédure enregistrée mais non exécutée dans cet environnement. Toute erreur future de compilation/analyse Flutter doit être corrigée avant clôture totale.

## Sécurité et limites explicites

- La sélection de l'institution et des rôles dans Flutter ne fait que guider l'interface. Chaque requête GET/POST est authentifiée et doit être autorisée par le backend.
- Les contrôles de confidentialité sont gouvernés côté serveur. Côté client, aucune inférence n'est calculée sur une donnée non publiée ; les snapshots masqués ne sont jamais déversés dans les widgets.
- La gestion de question/blueprint utilise les identifiants de référentiels existants ; pas de navigateur intégré de banque de questions dans ces panneaux. L'API serveur reste la source de vérité.
- L'aperçu CSV est volontairement borné, volatile, non enregistré sur appareil ; il ne s'agit pas d'un export en fichier local.
- Certificats PostgreSQL/Redis, charges concurrentes et appareil physique différés aux phases correspondantes.

## Décision

**Clôture backend local : OUI. Code frontend des deux phases : substantiellement développé, intégré. Clôture frontend vérifiée : NON (Flutter non exécuté).**
La Phase 16 reste non commencée selon la décision utilisateur.
