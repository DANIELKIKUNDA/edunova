# EduNova — Baseline v0.13.1

## LOT 12 — Ingestion industrielle

Baseline parent : **v0.12.1 LOT 11 Studio éditorial UI/UX maximal**.

### Contrats figés
- API : `0.13.1`.
- Flutter mobile/admin : `0.13.1+19`.
- PostgreSQL : migration `0009_ingestion_industrielle_v0_13_0.sql`.
- Le Studio reste privé et indépendant des universités.
- Aucun document OCRisé n'est publié automatiquement : la gouvernance LOT 11 reste obligatoire.
- Les droits de diffusion et le contexte académique font partie de la clé logique de déduplication.
- Les fichiers rejetés au préflight/antivirus ne doivent pas être conservés dans le staging.
- La queue PostgreSQL est autoritative ; l'API HTTP n'exécute jamais un OCR long dans la requête.

### Certification ChatGPT
- backend : **264/264 PASS** ;
- ingestion dédiée : **19/19 PASS** ;
- `compileall` : PASS ;
- audit LOT 12 : **64/64 PASS**.

### État
Backend/pipeline : **certifié dans l'environnement ChatGPT**.
Flutter Studio + infrastructure externe ClamAV/R2 + charge réelle : **OPEN-machine / OPEN-staging**.
