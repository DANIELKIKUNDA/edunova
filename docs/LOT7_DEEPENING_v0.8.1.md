# LOT 7 — Approfondissement v0.8.1

## Objectif
Transformer la synchronisation et la bibliothèque d’EduNova en expérience multi-appareils premium, explicable et robuste sur réseaux instables.

## Renforcements principaux
- accusé de réception (`acked_cursor`) par appareil ;
- inventaire et révocation d’appareils ;
- compaction serveur sûre, uniquement après accusé de tous les appareils actifs ;
- `retained_floor` + `reset_required` pour forcer un bootstrap canonique après longue absence ;
- snapshot bootstrap afin d’éviter de rejouer tout l’historique ;
- validation stricte des payloads et rejet récursif des chemins/fichiers privés ;
- pagination catalogue par curseur opaque et ETag stable ;
- suivi de cours (`course_follow`) synchronisable entre appareils ;
- diagnostic local de santé de synchronisation : pending, conflits, dead letters ;
- version/changelog visibles dans la fiche de cours ;
- limites de taille, batches bornés et frontières local-only/server-authoritative maintenues.

## Doctrine de confidentialité
Les PDF/images personnels, OCR/chunks personnels et conversations privées restent locaux. Le cloud synchronise uniquement les données légères explicitement autorisées.

## Règle de conflit
Aucun overwrite silencieux. L’utilisateur peut garder la version cloud ou la version locale ; toute reprise locale repart sur la version canonique actuelle.

## Statut
Backend : 181/181 tests PASS. Flutter : OPEN-machine jusqu’à génération Drift v13, analyse, tests et builds réels.
