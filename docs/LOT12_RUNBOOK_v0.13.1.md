# RUNBOOK LOT 12 — Exploitation

## Démarrage
- appliquer les migrations PostgreSQL jusqu'à `0009` ;
- configurer le bucket staging R2/S3 en production ;
- lancer ClamAV ;
- lancer API + au moins un `ingestion-worker` ;
- définir `INGESTION_SYSTEM_ACCOUNT_ID` si un compte technique est souhaité.

## SLO internes recommandés
- upload/preflight p95 < 5 s pour fichier raisonnable ;
- aucun job sans heartbeat > `INGESTION_LEASE_SECONDS` ;
- backlog le plus ancien < 30 min en régime normal ;
- dead-letter = 0 en régime nominal ;
- 100 % des OCR avec `needs_human_verification=true` relus avant publication.

## Incident : worker mort
Le lease expire ; le sweeper remet le job en retry ou dead-letter. Vérifier le motif `worker_lease_expired`.

## Incident : antivirus indisponible
L'upload échoue en 503. **Ne pas désactiver le fail-closed en production.** Réparer ClamAV puis réessayer.

## Incident : dead-letter
1. ouvrir le lot dans Studio ;
2. vérifier `last_error` ;
3. corriger dépendance/source ;
4. Owner clique « Réessayer » ;
5. vérifier que le lot repasse en `running`.

## Incident : checksum différent
Ne pas publier. Reconstituer l'origine du document et vérifier si le fichier a été remplacé/corrompu.
