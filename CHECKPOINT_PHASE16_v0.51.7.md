# EduNova v0.51.7 — Phase 16 / Alertes personnelles Campus

**Parent canonique :** `EduNova_v0.51.6_RC_PHASE16_CAMPUS_EVENT_REGISTRATIONS.zip` ; SHA-256 parent vérifié : `2a0017b63f668d4bad4a49e84918e90f4a0d14fcbdd80c3c639443593567d3fb`.

## Périmètre conservateur

Nouvelle vue de **consultation personnelle**, sans envoi de notifications externes : retards et échéances proches des emprunts physiques, annulations de réservations pour maintenance, événements imminents / annulés pour lesquels un utilisateur conserve une inscription active. Les écrans et règles métier existants sont réutilisés, sans second registre de prêts, de réservations ni de calendrier.

## Contrat de confidentialité

L'API dérive exclusivement `account_id` du bearer token, valide que l'institution et l'appartenance sont actives, puis applique **institution ET utilisateur** dans chaque requête SQL, même pour les administrateurs. Les messages affichés sont génériques : ni livre emprunté par autrui, ni noms de participants, ni données personnelles d'autres utilisateurs. Résultats limités à 50 alertes. Un affichage n'envoie ni SMS, ni e-mail, ni push et n'acquitte aucune notification.

L'application Flutter remet à zéro les alertes lors du changement d'institution, d'une fermeture / mise en arrière-plan et d'une erreur d'autorisation ; les réponses réseau périmées sont ignorées par la génération de chargement déjà en place.

## Limitations et validations futures

- Les alertes sont actualisées quand l'écran est consulté / rafraîchi ; aucune diffusion ni synchronisation hors ligne automatique.
- La source de réservations et d'inscriptions est bornée par pagination SQL ; les très longues histoires ne sont pas garanties exhaustives dans cette vue.
- La vérification Dart (`flutter analyze` et `flutter test`) n'a pas été exécutée ici (SDK absent). Les tests Dart sont ajoutés et seront exécutés sur un environnement équipé / CI.
- Les certifications PostgreSQL transactionnel, Redis, appareils physiques, stockage objet et fournisseurs restent hors de ce checkpoint.
- La Phase 16 demeure **ouverte** : intégration des réservations aux emplois du temps et réseau Alumni notamment.
- Les Phases 14/15 gardent leur réserve de validation Flutter.

Lire `RAPPORT_TECHNIQUE_PHASE16_v0.51.7.md` et `REGRESSION_BACKEND_v0.51.7.txt` avant toute certification.
