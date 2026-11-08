# EduNova v0.51.11 — GitHub Actions Phase 16

Base: v0.51.10. Ajout de `.github/workflows/phase16-certification.yml` : déclenchement manuel `workflow_dispatch`, push/PR ciblés, tests backend Phase 16 et audit structurel, analyse Flutter, tests Flutter machine-readable, compilation Flutter Web et dépôt d'artefacts même en cas d'échec. Permissions GitHub minimales, concurrence contrôlée et timeouts.

## Limites et preuves
- YAML parsé localement : valide.
- GitHub connecté interrogé : aucune installation de dépôt correspondant à EduNova trouvée. Aucun push ni exécution distante ne peut être revendiqué.
- SDK Flutter absent de cet environnement : tests et compilation Flutter NON exécutés localement.
- Une tentative de tests backend Phase 16 a été lancée mais a dépassé le délai de l'outil : ne pas l'interpréter comme PASS.
- Déclencher `EduNova Phase 16 Certification` depuis l'onglet Actions après dépôt du projet dans le dépôt GitHub approprié. Lire les artefacts des deux jobs et corriger tout échec avant certification.
