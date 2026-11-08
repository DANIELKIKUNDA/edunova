# EduNova v0.45.0 — Phase 10, première livraison : stages

## Portée effectivement réalisée

- Affectation d'un stage à un étudiant actif avec inscription académique active et encadrant Campus actif.
- Université strictement vérifiée, droits d'administration limités aux responsables académiques.
- Cycle gouverné : proposé → approuvé → actif → terminé ; annulation contrôlée.
- Historique des activités quotidiennes saisi par l'étudiant uniquement durant la période et l'état actif.
- Dates validées, justification obligatoire, verrouillage optimiste, unicité des journaux quotidiens.
- API `/v1/placements`, tables persistantes, migration 0069, tests de sécurité.

## Hors périmètre de cette première livraison

Les conventions signées, validation par l'organisme d'accueil, évaluation des maîtres de stage, soutenances, TFC/mémoires/thèses, versions documentaires et jurys de recherche ne sont PAS implémentés dans cette livraison. L'interface Flutter et les infrastructures externes ne sont PAS certifiées. Il ne faut pas annoncer la Phase 10 complète.

## Références de comparaison

Moodle Assignment : états brouillon/soumis, dépôt de fichiers et workflows de correction ; ces concepts sont utiles pour le futur suivi des mémoires, mais n'impliquent pas une intégration automatique de Moodle.
