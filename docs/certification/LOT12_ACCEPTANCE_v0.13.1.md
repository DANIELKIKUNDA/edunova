# LOT 12 v0.13.1 — critères d'acceptation

## Backend
- [x] modèle batch/document/job/result ;
- [x] upload idempotent ;
- [x] manifest immuable ;
- [x] préflight signature réelle ;
- [x] PDF chiffré rejeté ;
- [x] antivirus adapter ClamAV ;
- [x] staging local + S3/R2 ;
- [x] worker séparé ;
- [x] lease + heartbeat ;
- [x] retry + DLQ ;
- [x] récupération lease expiré ;
- [x] déduplication globale contextualisée ;
- [x] bundle photos multi-pages ;
- [x] SHA source + SHA artefact + version pipeline ;
- [x] projection Studio idempotente ;
- [x] audit lot ;
- [x] dashboard/SLA ;
- [x] preview OCR.

## UX Studio
- [x] section Ingestion ;
- [x] dashboard ;
- [x] création lot ;
- [x] import multiple ;
- [x] regroupement photos ;
- [x] progression ;
- [x] qualité OCR ;
- [x] retry dead-letter ;
- [x] action selon rôle ;
- [ ] certification Flutter Web machine ;
- [ ] revue responsive réelle 390/768/1024/1440 px ;
- [ ] test avec 200 fichiers réels ;
- [ ] test ClamAV/R2 staging réels.

## Durcissement final v0.13.1
- [x] snapshot canonique du manifeste persisté ;
- [x] SHA-256 du snapshot recalculable et vérifiable ;
- [x] contrôle des champs immuables des documents après gel ;
- [x] endpoint d'intégrité du manifeste ;
- [x] échec d'intégrité auditable ;
- [x] retry bulk des dead-letters Owner-only ;
- [x] migration PostgreSQL 0010 ;
- [x] tests backend dédiés ajoutés.
