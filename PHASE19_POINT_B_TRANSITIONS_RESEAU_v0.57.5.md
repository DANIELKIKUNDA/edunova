# EduNova — Phase 19 / Point B — Audit des transitions réseau (v0.57.5)

## Source
Base : archive complète v0.57.4.

## Correctifs
- `DownloadResource` : détection explicite de l'absence de réseau avant la demande de grant distant. La connectivité détectée n'est pas une garantie d'accès Internet : les erreurs réseau réelles restent gérées par le traitement existant.
- `RunDownloadQueue` : si l'appareil est hors réseau, l'opération reste dans la file sans consommer de tentative ; report de 30 secondes, état et message d'attente conservés. Les erreurs autres que `network_unavailable` conservent la politique de retry existante.

## Vérifications
- Tests backend de synchronisation : 17/17 PASS (9,07 s).
- Tests Flutter/Dart et compilation : NON EXÉCUTÉS (SDK absent).
- Revue statique du parcours : les métadonnées `ready` ne garantissent pas à elles seules la présence physique du fichier ; la lecture locale de toutes les ressources n'est pas démontrée par ce correctif.

## État
Point B : corrections de transitions réseau intégrées, mais pas de certification Flutter ni de parcours complet de lecture hors connexion. À vérifier lors du point C / tests sur environnement Flutter, et avant de certifier la Phase 19.
