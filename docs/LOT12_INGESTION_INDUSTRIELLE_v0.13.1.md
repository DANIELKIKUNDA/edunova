# LOT 12 — Ingestion industrielle, OCR par lots & productivité éditoriale

## 1. Objectif
Permettre à l'équipe EduNova de déposer 10, 100 ou 1 000 PDF/scans sans traitement manuel fichier par fichier et sans faire dépendre le serveur Web d'un OCR long.

## 2. Pipeline
1. Création d'un lot avec contexte académique et droits.
2. Upload idempotent.
3. Préflight signature/taille/pages/pixels.
4. Scan antivirus.
5. Déduplication SHA-256.
6. Manifest figé.
7. Création de jobs.
8. Claim par worker avec lease atomique.
9. Heartbeat pendant OCR long.
10. Extraction/OCR/structure/questions.
11. Artefact JSON versionné et hashé.
12. Création idempotente d'un brouillon Studio.
13. Relecture humaine / gouvernance LOT 11.

## 3. Sécurité d'entrée
- aucune confiance dans l'extension du fichier ;
- détection par signature réelle PDF/JPEG/PNG/WebP ;
- PDF chiffré rejeté ;
- limites configurables de taille, pages et pixels ;
- antivirus ClamAV obligatoire en production ;
- fichiers rejetés non conservés dans le staging ;
- clés de stockage protégées contre `../` ;
- rate limiting interne des uploads et retries.

## 4. Fiabilité
- idempotence via `Idempotency-Key` ;
- checksum source unique dans un lot ;
- déduplication globale uniquement si **contexte + droits** identiques ;
- retry exponentiel ;
- dead-letter après épuisement ;
- retry manuel Owner ;
- lease + heartbeat ;
- récupération automatique d'un worker mort ;
- job long jamais exécuté dans la requête HTTP.

## 5. Scans multi-pages
Plusieurs photos d'une interrogation peuvent être regroupées en un seul document logique. Chaque photo passe d'abord le préflight et l'antivirus, puis l'ensemble est converti en PDF multi-pages avant OCR.

## 6. Qualité & reproductibilité
Chaque résultat conserve :
- SHA-256 du fichier source ;
- SHA-256 de l'artefact extrait ;
- `pipeline_version` ;
- nombre de pages/sections/chunks/questions ;
- confiance OCR moyenne ;
- ratio de texte exploitable ;
- warnings qualité ;
- drapeau de vérification humaine.

## 7. Observabilité
Le Studio expose :
- backlog ;
- dead-letter ;
- document le plus ancien en attente ;
- SLA dépassé ;
- débit ;
- taux de réussite ;
- historique audit du lot.

## 8. UX opérateur
Section **Ingestion** dans EduNova Studio :
- dashboard opérationnel ;
- nouveau lot guidé ;
- upload multiple ;
- bundle de photos multi-pages ;
- progression du lot ;
- statut par document ;
- confiance OCR ;
- indication « vérification humaine requise » ;
- retry dead-letter ;
- preview OCR page 1 ;
- rôles visibles/actionnables selon Owner/Editor/Reviewer/Publisher.

## 9. Limites assumées
- l'upload Web v0.13.1 transite encore par l'API, mais est borné en mémoire par `INGESTION_MAX_FILE_BYTES` ;
- le staging production est déjà S3/R2-compatible ; une évolution future pourra signer des uploads directs navigateur→R2 si les volumes/bande passante le justifient ;
- Flutter Web Admin doit encore être compilé/certifié sur machine réelle.

## 10. Durcissement final v0.13.1
La clôture technique du LOT 12 ajoute quatre garanties de niveau production :
- **snapshot canonique du manifeste** conservé en base, et non plus seulement son empreinte ;
- manifeste couvrant contexte académique, droits, politique de préflight, version du pipeline et métadonnées immuables de chaque document ;
- **vérification d'intégrité à la demande** (`GET /v1/ingestion/batches/{id}/manifest/verify`) avec audit automatique en cas d'écart ;
- **reprise bulk des dead-letters** réservée à Owner, avec rate-limit et audit.

Le statut `succeeded` reste un statut **technique** d'ingestion. Il ne signifie jamais « publié ». Le résultat est projeté vers Studio pour poursuivre la gouvernance humaine du LOT 11 ; aucune ingestion ne contourne les quality gates éditoriaux.
