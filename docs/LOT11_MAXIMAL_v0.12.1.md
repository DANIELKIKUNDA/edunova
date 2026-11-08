# LOT 11 maximal — EduNova Studio v0.12.1

## Pourquoi ce durcissement
v0.12.0 posait une bonne gouvernance, mais l'interface restait trop proche d'une console de consultation. v0.12.1 transforme EduNova Studio en poste de travail éditorial complet.

## Workflow contrôlé
- création et métadonnées ;
- révision versionnée ;
- sources/provenance ;
- soumission en relecture ;
- checklist structurée ;
- corrections demandées ;
- approbation ;
- publication avec changelog ;
- archivage ;
- historique/audit.

## Qualité et séparation des responsabilités
### Standard
Checklist : traçabilité des sources, qualité structurelle, droits vérifiés.

### Médical / high-stakes
Checklist : exactitude factuelle, traçabilité, conformité au périmètre, qualité de langue, sécurité.

Auteur, relecteur et publicateur sont distincts. Une source OCR doit être vérifiée par une deuxième personne.

## Concurrence
Chaque `EditorialItem` porte un `row_version`. Les mutations du Studio transmettent `expected_version`. Si un autre utilisateur a modifié le contenu, l'API retourne `409 editorial_concurrent_modification` et l'interface recharge la fiche.

## UX Studio
- dashboard avec queues et retards ;
- recherche multi-champs ;
- filtres par état/type/risque ;
- pagination ;
- fiche détaillée ;
- six onglets cohérents ;
- contrôles qualité visibles ;
- actions selon rôle/état ;
- gestion de l'équipe ;
- session persistante avec refresh token ;
- navigation adaptative.

## Limite volontaire
LOT 11 ne fait pas l'ingestion massive de centaines de fichiers. Ce chantier appartient au LOT 12 afin de préserver la séparation des responsabilités : LOT 11 gouverne, LOT 12 industrialisera l'entrée de masse.
