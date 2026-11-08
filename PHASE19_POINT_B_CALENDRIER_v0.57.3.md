# EduNova v0.57.3 — Phase 19, point B : calendrier

## Modifications
- Messages d’échec de chargement et boutons Réessayer pour les échéances et l’horaire.
- Gestion des erreurs de sauvegarde des événements et des cours : retour visible à l’étudiant.
- Validation du titre et de l’intervalle horaire ; refus des heures impossibles et des intervalles inversés.

## Vérifications
- Tests backend de synchronisation : 17/17 PASS.
- SDK Flutter/Dart absent : compilation et tests Flutter NON EXÉCUTÉS.
- L’audit des parcours de lecture hors connexion et des transitions réseau reste à effectuer ; point B non clôturé.

## Réserves
- Les écrans de dialogue sont fermés avant confirmation de la sauvegarde ; en cas d’erreur, les données saisies doivent être ressaisies.
- La méthode `_parse` conserve une valeur de repli pour un champ non modifié ; les entrées invalides modifiées sont rejetées.
