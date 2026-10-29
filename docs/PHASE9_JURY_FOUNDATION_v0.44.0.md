# EduNova 0.44.0 — Phase 9, fondation Jury & délibérations

## Périmètre livré
- Sessions institutionnelles de jury, liées à une université, cohorte, curriculum publié et année académique.
- Autorisation Rector / Owner / Academic Admin; accès refusé aux enseignants et aux autres membres.
- Calcul initial sur inscriptions ECUE canoniques, sans créer de second Gradebook.
- Crédits reconnus uniquement pour ECUE VALIDATED/EXEMPTED; résultat DEFERRED si un ECUE demeure ENROLLED.
- Seuil minimal de crédits configuré par session (règle institutionnelle à paramétrer, aucun seuil juridique inventé).
- Empreinte SHA-256 déterministe de la preuve académique; contrôle anti-obsolescence au verrouillage et à la publication.
- Cycle DRAFT → LOCKED → PUBLISHED, contrôle de version optimiste, décisions persistantes, traçabilité audit.
- Migration 0067, API /v1/jury, 8 tests adversariaux supplémentaires.

## Limites explicites — pas encore une certification complète Phase 9
- Le calcul de crédits est une première règle configurable; il ne remplace pas les règlements officiels de chaque université.
- Quorum, composition et votes des membres, validation collective, signatures et procès-verbaux officiels non implémentés.
- Sessions de rattrapage et exceptions motivées nécessitent encore une modélisation gouvernée.
- Correction d'une décision existante: non autorisée dans cette première tranche, doit passer par un workflow versionné.
- L'immuabilité du curriculum et du résultat final est applicative; mécanismes supplémentaires de verrouillage transactionnel PostgreSQL restent à certifier.
- Flutter et intégrations réelles non certifiés ici.

## Références de conception
- Oracle PeopleSoft Student Records — academic standing rules / effective term.
- Oracle PeopleSoft Academic Advisement — suivi des exigences du diplôme.
- UCLouvain — règlement des études et examens, responsabilités des jurys (contexte comparatif, non substitut aux règlements congolais).

## Certification
Voir exécution locale pytest, compileall, audit LOT32 et contrat des migrations. Ne pas présenter cette livraison comme un moteur de délibérations institutionnelles complet.
