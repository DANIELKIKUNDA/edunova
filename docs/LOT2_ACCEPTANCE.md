# LOT 2 — Critères de certification

## A. Pipeline documentaire

- [x] D2-01 Empreinte SHA-256 déterministe.
- [x] D2-02 Extraction native d'un PDF texte.
- [x] D2-03 OCR d'une image/photo.
- [x] D2-04 OCR de secours prévu pour pages PDF scannées.
- [x] D2-05 Normalisation texte et suppression de césures de ligne.
- [x] D2-06 Détection de chapitres/sous-chapitres.
- [x] D2-07 Construction de chunks avec pages sources.
- [x] D2-08 Recherche textuelle pondérée.
- [x] D2-09 Rapport qualité et confiance OCR.
- [x] D2-10 Artefacts JSON/JSONL auditables.
- [x] D2-11 Tests automatiques backend : 11/11 PASS dans l'environnement ChatGPT.

## B. Persistance et domaine Flutter

- [x] D2-12 Schéma Drift v2 : analyses, sections, chunks, annotations, progression.
- [x] D2-13 Migration v1 -> v2 définie.
- [x] D2-14 Port `LocalDocumentAnalysisEngine` défini.
- [x] D2-15 Mode de confidentialité `deviceOnly` / `onlineAssist` défini.
- [x] D2-16 Repository annotations/progression implémenté.
- [ ] D2-17 Génération Drift réelle sur SDK Flutter.
- [ ] D2-18 `flutter analyze` PASS.
- [ ] D2-19 `flutter test` PASS.

## C. Lecteur premium

- [x] D2-20 Route dédiée document workspace.
- [x] D2-21 Lecture image native in-app.
- [x] D2-22 Adaptateur PDF in-app préparé (`pdfrx`).
- [x] D2-23 Signets persistants.
- [x] D2-24 Panneau chapitres.
- [x] D2-25 Panneau annotations/repères.
- [x] D2-26 Barre d'actions Résumé / Audio / Quiz / Assistant.
- [ ] D2-27 Navigation/résumé de page certifiés sur vrai SDK Flutter.
- [ ] D2-28 Surlignage texte précis certifié.
- [ ] D2-29 Recherche locale branchée sur chunks Drift.
- [ ] D2-30 Reprise exacte à la dernière page certifiée.

## D. OCR local et PWA

- [ ] D2-31 OCR local Android certifié.
- [ ] D2-32 OCR local iOS certifié.
- [ ] D2-33 OCR local Windows certifié.
- [ ] D2-34 OPFS PWA certifié.
- [ ] D2-35 OCR/extraction PWA offline certifiés.

## Règle de fermeture

**LOT 2 ne peut être déclaré CLOSED tant que tous les critères obligatoires de B, C et D pour la cible de lancement ne sont pas PASS.**

Les cases non cochées sont des travaux connus et planifiés maintenant ; elles ne constituent pas des « ajouts tardifs ».
