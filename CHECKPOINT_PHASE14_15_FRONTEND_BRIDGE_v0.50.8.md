# EduNova v0.50.8 — Reprise frontend fonctionnelle des phases 14 et 15

**Source canonique :** v0.50.7, Phase 15 backend closure. **Phase 16 non commencée.**

## Nouvelle règle de clôture adoptée
Une phase fonctionnelle ne peut être déclarée entièrement clôturée tant que le backend ET les interfaces Flutter correspondantes ne sont pas effectivement intégrés et vérifiés. La Phase 19 conserve sa spécialisation mobile/offline/UX transverse. La certification sur appareils réels reste en Phase 23. Les infrastructures externes gardent leurs phases de certification.

## Travaux réels v0.50.8
- Inspection du code Flutter existant : écran Campus essentiellement déclaratif, malgré des API Phases 14/15 opérationnelles.
- Connexion de l'espace Campus aux appartenances universitaires réelles (`/v1/campus/me/institutions`) et à l'état de membership ; aucune saisie libre du tenant.
- Espace **Intelligence pédagogique** : sélection des enseignements autorisés ; consultation du tableau d'objectifs, priorités d'intervention, tendances descriptives, erreurs récurrentes et rapprochement informatif gradebook.
- Espace **Intelligence institutionnelle** : indicateurs gouvernés, statut des sources, confidentialité des suppressions, priorités humaines, période de référence et comparaison contrôlée de deux périodes.
- Compte et jeton existants réutilisés, rafraîchissement d'accès, authentification sur tous les GET ; identification et restrictions finales contrôlées côté serveur.
- La consultation de l'intelligence se fait **en ligne sans écriture dans Drift/local storage** ; états vidés au changement de contexte et contrôle d'appartenance avant les données sensibles.
- Restitution des valeurs supprimées ou non comparables en « Masqué / non disponible » et « Comparaison indisponible », jamais en 0 %.
- Tests du contrat FastAPI et tests Flutter source (unitaires et widgets) ajoutés.

## Vérifications exécutées
- Python pytest backend complet : **891 passed / 0 failed**, 248.13 s, code de sortie 0.
- Tests backend ciblés de contrat front–API : **2 passed**, 6.15 s.
- Compilation bytecode du code Python : PASS.
- Contrôle statique spécifique de présence des routes, classes, garde-fous et fichiers de tests : PASS ; **ce n'est PAS le compilateur Dart**.
- Flutter SDK / dart introuvables ici : **flutter analyze, flutter test et flutter build NON EXÉCUTÉS**, les tests Flutter n'ont donc pas le statut PASS.
- Aucun test PostgreSQL réel, Redis réel, stockage objet, appareil physique ni certification production exécuté.

## Réserve essentielle
**Les phases 14 et 15 restent « backend local clôturé / frontend en intégration non certifiée », non « fonctionnellement clôturées ».** Les écrans lecture seule sont implémentés, mais la couverture Flutter exhaustive des fonctions de gestion d'objectifs, d'archives/exports et les vérifications Dart, responsive sur appareils et E2E restent à compléter. Le projet n'a pas démarré la Phase 16.

La première exécution de la régression concurrente avec un pytest ciblé a été corrompue par collision de la même base SQLite `.pytest_edunova.db` (54 échecs au premier passage). Les processus concurrents ont été arrêtés/terminés, un passage ciblé seul a réussi, puis la **régression finale isolée** s'est terminée à 891/891 PASS. Cet incident n'est pas masqué dans les preuves.

Dernière migration SQL : `0085` (inchangée dans v0.50.8).
