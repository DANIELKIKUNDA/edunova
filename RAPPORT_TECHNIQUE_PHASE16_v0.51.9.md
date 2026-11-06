# EduNova v0.51.9 — Phase 16 : consolidation fonctionnelle et contrôles de clôture

## Provenance et décisions

Base canonique **v0.51.8** : `EduNova_v0.51.8_RC_PHASE16_ACADEMIC_ALUMNI_FRONTEND_INTEGRATION.zip`.
La roadmap Edunova v1.0 reste inchangée ; les modules de calendrier, de séances d'enseignement, de campus et d'Alumni ont été réutilisés. Aucune migration SQL nouvelle ; la dernière migration demeure **0095**.

## Développements backend réellement implémentés

### Réconciliation des ressources académiques

Ajout dans le repository SQL, le service et l'API authentifiée de `GET /v1/campus-services/institutions/{institution_id}/academic-unassigned`.
Ce point d'accès, réservé aux rôles administratifs institutionnels, liste les **événements futurs programmés** et les **séances futures planifiées** sans affectation physique existante. Il calcule les comptes complets, retourne les cent premiers éléments ordonnés par type et indique `truncated` si ce plafond est dépassé. Les événements annulés et séances terminées sont exclus ; les universités ne peuvent consulter les données d'autrui. Aucune affectation automatique n'est créée à partir des libellés libres de salles.

L'interface Flutter « Salles académiques » consulte ce rapport et propose les séances réelles à affecter aux ressources autorisées. La connexion au mécanisme transactionnel de réservation et à ses contrôles de chevauchement demeure inchangée. Le rapport recense les séances non affectées sans déclarer qu'elles sont toutes déjà réconciliées.

### Alumni des anciens diplômés sans inscription active

Ajout de la consultation SQL des **universités des profils Alumni vérifiés du compte authentifié**, puis revalidation de l'activité institutionnelle et du statut de l'adhésion. Point d'accès authentifié : `GET /v1/campus-services/alumni/my-institutions`.

- Aucun annuaire global d'universités n'est exposé par cette route.
- Les profils non vérifiés et les profils d'autrui ne donnent aucun accès.
- Les adhésions explicitement **suspendues ou révoquées** excluent l'accès, même si le profil Alumni a été vérifié auparavant.
- Le diplômé sans adhésion active peut consulter son réseau déjà vérifié, mais ne peut pas modifier son profil sans appartenance active.
- La réponse se limite au nom et à l'identifiant de l'université autorisée ; aucune référence documentaire ni donnée personnelle d'autrui.

L'écran Flutter Campus propose désormais « Mes universités Alumni vérifiées » indépendamment de la liste des adhésions actives. L'écran Alumni désactive l'édition pour les diplômés sans adhésion active. Les protections du serveur restent déterminantes.

## Tests et vérifications exécutés

| Vérification | Résultat |
|---|---|
| Régression globale backend après modifications backend | **1062/1062 PASS**, durée **229,18 s**, code de sortie **0** |
| Nouveaux tests adversariaux et positifs ciblés v0.51.9 | **5/5 PASS** |
| Audit structurel spécifique de clôture | **22/22 PASS** |
| Audit existant statique Flutter Phase 14/15 | **33/33 PASS** (non compilateur) |
| Compilation syntaxique Python application + tests | PASS |
| Lecture du workflow GitHub Actions avec PyYAML | PASS : job Flutter configuré |
| Flutter analyze / flutter test / flutter build web | **NON EXÉCUTÉS** : SDK Flutter/Dart absent |
| PostgreSQL réel, Redis, object storage, appareils physiques | **NON EXÉCUTÉS** |

Cas adversariaux des nouveaux tests : accès d'un autre étudiant au réseau Alumni, profil en attente ou rejeté, suspension et révocation de l'appartenance, institution inactive, impossibilité de modifier le profil sans appartenance active, contrôle RBAC des séances non affectées, indépendance multi-universités, filtrage des séances expirées/annulées, limitation et exhaustivité des comptes, identité de l'appelant issue du bearer token.

## Réserves et critère de clôture maximale

**Phase 16 : consolidation fonctionnelle approfondie ; pas encore clôturée au niveau maximal.**

Le SDK Flutter/Dart n'était pas installé sur cette machine. Les nouveaux tests de contrat Flutter sont présents dans `apps/mobile/test/campus_academic_alumni_gateway_test.dart` et le pipeline CI contient `flutter analyze`, `flutter test`, `flutter build web` ; aucune réussite distante de ce pipeline n'a été observée ici. Une compilation réellement exécutée et des corrections si nécessaire restent nécessaires pour déclarer la clôture backend + frontend selon la règle du projet.

Les affectations des **séances historiques sans lien explicite à une ressource** doivent être réalisées par les responsables sur les vrais dossiers universitaires. Les rapports détectent le travail à faire sans deviner des ressources depuis le champ libre `location`. La logique PostgreSQL transactionnelle est écrite mais non certifiée contre un vrai serveur concurrent dans cette itération.

La certification sur appareils reste planifiée en Phase 23. Les Phases 14/15 conservent également leur réserve de compilation Flutter. La Phase 17 n'a pas commencé.
