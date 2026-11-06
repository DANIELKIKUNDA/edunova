# RAPPORT TECHNIQUE — EDUNOVA v0.50.8

**Livraison :** Intégration initiale réelle backend/Flutter des Phases 14 et 15, sans refonte de l'architecture ni changement de roadmap.

## Source inspectée
`EduNova_v0.50.7_RC_PHASE15_BACKEND_CLOSURE.zip` (1 316 entrées dans le checkpoint source). Le code contient deux applications Flutter (`apps/mobile`, `apps/admin`). Dans `apps/mobile`, le point d'entrée institutionnel `campus_page.dart` n'offrait pas auparavant de navigation réelle vers les API des phases récentes. La plateforme `apps/admin` cible le centre Volcano Tech et l'éditeur ; aucun privilège d'administration d'université n'a été présumé dans cet espace.

## Implémentations
| Domaine | Fichier | Contrat / sécurité |
|---|---|---|
| Gateway Ph14/15 | `apps/mobile/lib/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart` | API Dio authentifiée, rafraîchissement du jeton, URI validées, aucun enregistrement offline |
| Portail Campus | `apps/mobile/lib/src/features/campus/presentation/campus_page.dart` | liste institutionnelle effective, boutons réservés membres actifs de rôles autorisés |
| Ph14 enseignants | `apps/mobile/lib/src/features/campus_intelligence/presentation/institution_intelligence_page.dart` | objectifs, tendances, erreurs récurrentes, actions et intégrité des candidats gradebook |
| Ph15 direction | idem | statut de confidentialité, indicateurs, sources, recommandations et comparaison de périodes |
| Navigation | `apps/mobile/lib/src/app/router.dart` | route tenant contextuelle, entrée validée de nouveau contre l'appartenance serveur |
| Injection | `apps/mobile/lib/src/core/di/providers.dart` | réutilise client API et session identité existants |
| Backend contrat | `services/api/tests/test_phase14_15_frontend_route_contract.py` | 7 routes GET, dépendance explicite à `current_auth`, non-mutation des routes analytiques |
| Dart tests | `apps/mobile/test/campus_intelligence_*_test.dart` | URL/token, abus d'ID, non-auth, contrôle d'accès de navigation, valeurs confidentielles |

## Frontières d'autorisation
Les restrictions Flutter ne constituent PAS le contrôle d'accès. Les API réelles appliquent les permissions institutionnelles, l'isolement multi-universités et les limites des statistiques. Un ID d'université dans l'URL n'accorde aucun accès. Les décisions de confidentialité et l'accès aux données restent au backend.

## Périmètre exclu
Absence de modification de notes, d'inscription, de délibération et de sources d'analyses. Aucun nouveau schéma SQL. Aucun certificat d'anonymisation complète. L'interface Flutter de gestion des objectifs, associations question–objectif, export et gestion des archives demande encore une passe ; la compilation Flutter et la validation responsive/device n'ont pas eu lieu ici.

## Exécution et niveau de preuve
Régression finale backend : **891 PASSED**, exit 0, 248.13 s. Python compileall : PASS. Vérification statique de correspondance entre sources : PASS. Tests Dart écrits mais **non exécutés** car Flutter/Dart absents. PostgreSQL, Redis et appareils réels non certifiés. Au cours de l'exécution, un pytest parallèle a provoqué un conflit SQLite ; une régression isolée propre a ensuite réussi. Ne pas lire le nombre de tests backend comme une certification Flutter.

## Décision
Checkpoint v0.50.8 = **développement Flutter réalisé, certification frontend en attente**. Conserver la fermeture backend locale des Phases 14/15 mais retirer toute notion de clôture fonctionnelle totale tant que les tests Dart et les fonctionnalités restantes du frontend ne sont pas confirmés. Ne pas entamer la Phase 16 avant cet alignement.
