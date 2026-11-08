# EduNova v0.50.6 — Checkpoint canonique Phase 15

**Origine :** v0.50.5, ZIP original SHA-256 `92e51581f06af42bad443e21c84bd6b80facdba41d6d5f26e34b4b4104832cc0`.

- **Phase 15 en cours** ; Phase 16 non commencée ; roadmap 0–26 inchangée.
- Nouvel archivage statistique v4 : attestation HMAC de la population active à la capture, revérification à chaque lecture, retrait des archives v1–v3, exposition du payload de la seule archive la plus récente.
- Protection contre le changement d'identité des étudiants lorsque les effectifs restent identiques ; absence de publication du nonce, de la preuve ou d'identifiants étudiants.
- Comparaison des archives temporelles masquées, sans détection trompeuse de variations nominatives ; RBAC et isolation par université inchangés.
- Aucun changement de schéma. Dernière migration **0084**.
- Rapport : `RAPPORT_TECHNIQUE_PHASE15_v0.50.6.md`. Preuves : `TEST_EVIDENCE_PHASE15_v0.50.6.txt`.
- Non certifié : résistances temporelles transversales (dashboard live), PostgreSQL/Redis réels, Flutter, appareils, charge et fournisseurs.

- Certification locale : **878/878 tests backend PASS**, audit **17/17 PASS**, compilation Python PASS. Les résultats détaillés et limites sont dans le rapport et les preuves jointes.
