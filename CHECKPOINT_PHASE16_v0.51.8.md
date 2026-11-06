# EduNova v0.51.8 — Phase 16 / Liaisons académiques et Alumni

Parent canonique : `EduNova_v0.51.7_RC_PHASE16_CAMPUS_PERSONAL_ALERTS.zip`.

## Portée du checkpoint

**Affectations Campus :** liaison explicite d'une salle/laboratoire aux entités déjà existantes `campus_calendar_events` et `teaching_sessions`, sans deuxième module d'emploi du temps. Réservation, calendrier et séance vérifient les conflits dans une transaction et verrouillent la ligne de ressource. Libération versionnée. Une maintenance ne peut pas immobiliser silencieusement une salle où une séance future affectée est programmée. Les séances annulées n'occupent plus la ressource.

**Alumni :** profils opt-in par université, demande et examen par administration universitaire, référence de dossier interne, annuaire ne montrant que les profils validés **et** consentants, opportunités publiées/retraitées par le personnel autorisé. Un compte ne peut pas valider son propre profil. Une modification de profil réinitialise sa vérification. Les membres devenus inactifs (sans appartenance) conservent l'accès au réseau seulement si leur profil a été vérifié; une révocation ou une suspension explicite interdit l'accès. Les dossiers historiques/diplômes ne sont **pas** certifiés automatiquement : la validation est administrative et l'intégration aux documents officiels ne constitue pas une preuve de vérification cryptographique.

**Flutter :** vues Alumni et Salles académiques, connectées aux API avec authentification bearer, non-mise-en-cache, traitement des refus, invalidation des requêtes anciennes lors des changements de contexte; nouveaux tests de contrats API Dart. Workflow CI adapté pour exécuter `flutter analyze`, `flutter test`, `flutter build web --release` sur un runner équipé.

## Limites et politique de clôture

- Seuls les cours, séances et événements explicitement liés à une ressource contrôlent son occupation ; les libellés libres de salle et les horaires non affectés ne permettent pas d'identifier avec certitude une ressource physique.
- Les nouvelles réservations et affectations sont contrôlées par verrouillage de la ressource parent sur PostgreSQL, mais **aucun test de concurrence PostgreSQL réel n'est prétendu**.
- Les accès Alumni sans appartenance académique active exigent un profil auparavant vérifié ; le catalogue d'universités pour ces anciens membres et les parcours de réactivation sont un point d'intégration encore à approfondir.
- Les certifications Flutter/Dart effectives ne peuvent être clôturées localement sans SDK. La présence des fichiers et les contrôles statiques ne prouvent pas la compilation Flutter. Vérification sur appareils physiques réservée à la Phase 23.
- Pas de SMS, push ou e-mail externe, pas de traitement automatique des diplômes ni de vérification légalement qualifiée.

## Vérifications

Voir `RAPPORT_TECHNIQUE_PHASE16_v0.51.8.md` et `PREUVES_TESTS_v0.51.8.txt` : commandes effectivement lancées, résultats et réserves. Aucune déclaration globale de clôture Flutter/Phase 16 tant que l'exécution Flutter n'a pas abouti.
