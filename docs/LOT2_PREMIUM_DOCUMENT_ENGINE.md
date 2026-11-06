# LOT 2 — Moteur documentaire premium

Version de travail : **0.3.0**

## Objectif

Transformer un PDF, un scan ou une photo en ressource d'étude exploitable sans dégrader la confidentialité. Le moteur documentaire n'est pas un simple lecteur PDF : il doit produire une représentation structurée, traçable, recherchable et réutilisable par les modules Résumé, Audio, Quiz, Flashcards, Assistant et RAG.

## Pipeline cible

`fichier -> empreinte SHA-256 -> extraction native -> OCR si nécessaire -> normalisation -> contrôle qualité -> détection de chapitres -> chunks -> index local/RAG -> lecteur -> annotations -> progression -> dérivés pédagogiques`

Aucune étape générative n'est obligatoire pour pouvoir lire, rechercher ou structurer un document.

## Décisions verrouillées

1. **Idempotence documentaire** : un même fichier produit la même empreinte et le même `document_id` déterministe.
2. **Extraction native d'abord** : l'OCR n'est utilisé que lorsqu'une page n'a pas assez de texte exploitable.
3. **OCR hybride** : les PDF mixtes peuvent contenir pages texte + pages scannées ; la provenance est conservée page par page.
4. **Contrôle qualité** : pages vides, taux de texte exploitable, confiance OCR et avertissements sont persistés.
5. **Structuration déterministe** : chapitres/sous-chapitres sont détectés avant toute IA générative.
6. **Chunks auditables** : chaque chunk conserve ses pages et sa section d'origine.
7. **Confidentialité par défaut** : les documents personnels restent locaux. Une analyse en ligne d'un document privé nécessite un consentement explicite `onlineAssist`.
8. **Aucun upload silencieux** : aucun endpoint d'upload de document privé n'est exposé dans LOT 2.
9. **Lecteur in-app** : PDF/images sont consultés dans EduNova, pas exportés vers une autre application.
10. **Pas de verrou fournisseur** : OCR, index et IA restent derrière des ports/adaptateurs.

## Backend / pipeline partagé

Implémenté dans `services/api/app/modules/document_engine` :

- extraction PDF via PyMuPDF ;
- OCR Tesseract avec prétraitement OpenCV ;
- normalisation Unicode/espaces/césures ;
- détection de titres selon taille, graisse, numérotation et casse ;
- construction hiérarchique des sections ;
- chunking avec chevauchement ;
- estimation de tokens ;
- recherche textuelle pondérée ;
- rapport qualité ;
- génération d'artefacts JSON/JSONL ;
- CLI `scripts/process_document.py`.

Cette implémentation sert :

- aux ressources EduNova partagées ;
- aux imports administratifs ;
- à l'analyse distante facultative d'un document personnel avec consentement.

## Application Flutter

Nouveaux modèles locaux :

- analyse documentaire ;
- sections ;
- chunks texte ;
- annotations ;
- progression de lecture.

Le workspace premium fournit :

- lecture privée dans l'application ;
- signets ;
- panneaux Chapitres / Mes repères ;
- actions Résumé / Audio / Quiz / Assistant ;
- persistance prévue de la progression ;
- ouverture depuis `Mes documents`.

## Adaptateurs locaux par plateforme

La frontière `LocalDocumentAnalysisEngine` est définie avant implémentation pour empêcher les dépendances plateforme de contaminer le domaine.

### Android / iOS

Cible : extraction et OCR locaux, sans serveur lorsque le mode `deviceOnly` est sélectionné.

### Windows

Cible : extraction PDF locale + OCR local Tesseract ou moteur embarqué équivalent.

### Web/PWA

Cible : OPFS + extraction/OCR local WebAssembly lorsque possible. L'analyse distante reste une option explicite, jamais un comportement implicite.

## Pourquoi LOT 2 n'est pas déclaré certifié Flutter dans cet environnement

Le SDK Flutter n'est pas installé dans l'environnement courant. Les composants Dart/Flutter sont donc intégrés au dépôt mais ne doivent être marqués PASS qu'après :

- `flutter pub get` ;
- génération Drift ;
- `flutter analyze` ;
- `flutter test` ;
- build Android ;
- test réel d'un PDF texte ;
- test réel d'un PDF scanné ;
- test réel d'une photo d'interrogation ;
- test de reprise de lecture ;
- test offline ;
- test PWA/OPFS séparé.

Cette règle évite de qualifier de « terminé » un lot non compilé.
