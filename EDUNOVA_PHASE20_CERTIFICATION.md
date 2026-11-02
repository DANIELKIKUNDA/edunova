# EduNova — Rapport de certification Phase 20

Date: 2 novembre 2026  
Branche: `codex/phase20-industrialisation-fiabilite`  
Révision fonctionnelle certifiée: `4e49f83955ab207fafeea65cf8dfc51107f239d2`  
Base: `import/edunova-v0.57.12` (`ef3d52fb149067cd46fbd433370cddba05982afa`)

## 1. État vérifié à la reprise

- `main` ne contenait que le commit initial; la base réelle de développement était `import/edunova-v0.57.12`.
- La PR #1 documentait une certification Phase 19 partielle.
- Les chiffres historiques (1 201 backend, 32 finance, 34 PostgreSQL réel, 55 audits, 96 mobile, 2 admin et six builds) ont été retrouvés dans les rapports du dépôt. Ils ne sont pas assimilés à une nouvelle exécution.
- Aucun issue GitHub ouvert n'était présent lors de l'audit.
- Les correctifs Phase 20 ci-dessous n'étaient pas publiés sur la branche de référence.

## 2. Corrections Phase 20

### Téléchargements fiables

- validation du statut partiel et de l'en-tête `Content-Range` avant reprise;
- abandon du fragment local si le serveur répond sur une plage incohérente;
- conservation des validations taille, ETag et SHA-256 avant finalisation;
- politique de reprise bornée sans double consommation du budget lors d'une panne réseau transitoire.

### Offline-first et synchronisation

- maintien en file de l'opération lorsque le réseau est indisponible;
- absence d'incrément artificiel du nombre d'échecs hors ligne;
- tests de contrat sur la prévention des doublons et la reprise.

### Observabilité et sécurité

- événements JSON structurés, identifiant de corrélation contrôlé et durée des requêtes;
- neutralisation des retours ligne et bornage des valeurs;
- masquage de `Authorization`, cookies, mots de passe, jetons, secrets et clés API;
- dépendances `urllib3` et `msgpack` corrigées;
- image d'exécution débarrassée des copies vulnérables embarquées par pip/setuptools;
- scanner Trivy corrigé vers une version officielle disponible;
- Tesseract explicitement installé dans les runners backend afin que les scénarios OCR soient réellement exécutés.

### Compatibilité Flutter

- correction du composant d'espace d'étude pour fournir un ancêtre `Material` aux `ListTile`;
- analyse statique conservant les erreurs et avertissements bloquants, avec l'information de dépréciation Drift web rendue non bloquante;
- compilation Flutter web maintenue dans les workflows.

## 3. Résultats exécutés

### GitHub Actions — révision fonctionnelle `4e49f83`

| Workflow / contrôle | Résultat vérifié |
|---|---:|
| EduNova CI | succès |
| Backend complet | 1 207 réussis, 17 ignorés, 6 avertissements tiers |
| Flutter mobile complet | 96 réussis |
| Tests ciblés Flutter gouvernance | 7 + 4 réussis |
| Flutter Admin | 2 réussis |
| Build Flutter Web (CI) | réussi |
| Build conteneur API | réussi |
| Phase 19 technique | succès |
| Régression sécurité/synchronisation Phase 19 | 31 réussis |
| Phase 16 certification | succès |
| Régression backend complète Phase 16 | 1 207 réussis, 17 ignorés |
| Build Flutter Web Phase 16 | réussi |
| Phase 17 gouvernance | succès |
| Audit dépendances | succès |
| Scan Trivy de l'image | succès |

Exécutions GitHub: CI #97, Security #97, Phase 19 #43, Phase 16 #89, Phase 17 #82.

### Exécution locale complémentaire

- backend: 1 175 réussis, 0 échec (socle local synchronisé avant les dernières publications);
- tests ciblés Phase 20: 37 réussis;
- compilation Python: réussie.

Les résultats GitHub ci-dessus priment pour la révision publiée.

## 4. Limites et travaux restant ouverts

- Aucun nouveau test contre une instance PostgreSQL réelle n'a été exécuté dans cette mission; les 34 tests historiques restent une preuve antérieure.
- Aucun profilage sur appareil Android/iOS modeste réel n'a été exécuté.
- Les builds natifs Android, iOS et desktop n'ont pas été refaits; les preuves nouvelles couvrent Flutter Web et l'image conteneur.
- `drift/web.dart` reste une dette technique. La migration vers WasmDatabase doit inclure les artefacts wasm/worker et une recette de migration des données navigateur.
- Les 17 tests backend ignorés doivent être examinés séparément avant une certification globale sans réserve.
- Les six builds historiques n'ont pas tous été reproduits.

## 5. Verdict

**Phase 20: implémentation logicielle validée et intégrable, certification globale encore partielle.**

Les axes fiabilité des téléchargements, reprise hors ligne, observabilité, sécurité de la chaîne asynchrone et non-régression sont couverts par du code et des tests verts. Une certification complète de la plateforme reste conditionnée à PostgreSQL réel, aux builds natifs et au profilage sur appareils modestes. La PR demeure en brouillon et ne doit pas être fusionnée sans revue.
