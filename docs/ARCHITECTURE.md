# Architecture EduNova

## 1. Principes

1. Offline-first : l’étudiant peut lire, réviser et enregistrer sa progression sans réseau.
2. Local-first pour les documents personnels : le PDF/photo original reste sur l’appareil par défaut.
3. Backend indépendant des fournisseurs : IA, OCR, Mobile Money et stockage sont des ports.
4. Idempotence des paiements et synchronisations.
5. Architecture modulaire : chaque domaine évolue indépendamment.
6. Coût maîtrisé : pré-génération/cache des contenus communs ; IA seulement quand elle apporte une valeur nouvelle.

## 2. Bounded contexts

### Identity
Compte, session, appareils, préférences.

### Academic Profile
Faculté/domaine, filière, niveau, semestre, parcours actif, exploration en avance.

### Content
Cours EduNova, documents personnels, PDF, photos, chapitres, anciens sujets.

### Learning
Lecture, flashcards, quiz, erreurs, exercices, progression.

### Planning
Horaire, interrogations, examens, tâches, priorités quotidiennes.

### Readiness
Score explicable de préparation par évaluation.

### Subscription
Gratuit/Premium 30 jours, quotas, crédits IA.

### Payments
Transactions Mobile Money, webhooks, idempotence, renouvellement.

### Intelligence
RAG, assistant, résumé, génération contrôlée, routeur multi-fournisseurs.

### Sync
Outbox locale, synchronisation, conflits, reprise réseau.

## 3. Hexagone backend

- `domain`: entités, value objects, règles pures.
- `application`: cas d’utilisation/orchestration.
- `ports`: contrats requis par l’application.
- `infrastructure`: PostgreSQL, Redis, fournisseurs externes.
- `api`: adaptateur entrant HTTP.

Règle : `domain` n’importe jamais FastAPI, SQLAlchemy, Redis ou SDK tiers.

## 4. Mobile

Chaque feature contient :

- `domain`
- `application`
- `infrastructure`
- `presentation`

La couche UI ne parle pas directement à SQLite ni à HTTP.

## 5. Données privées

Les documents personnels restent locaux par défaut. L’utilisateur doit déclencher explicitement une analyse IA distante. Le serveur ne conserve pas automatiquement le fichier original personnel.

## 6. Sécurité

- Argon2id pour les mots de passe.
- Refresh tokens rotatifs.
- HTTPS.
- Secrets côté serveur uniquement.
- Chiffrement local des contenus Premium sensibles.
- Paiements confirmés uniquement par le backend.
- Journaux d’audit pour actions critiques.

## 7. Évolutivité

Le VPS pilote peut héberger API/PostgreSQL/Redis. À mesure que la charge augmente : base managée, workers horizontaux, stockage objet, CDN, observabilité centralisée.

## LOT 7 — Synchronisation et bibliothèque
Le protocole Sync est un port séparé du domaine financier et du stockage documentaire privé. Les clients publient des mutations idempotentes, reçoivent une version canonique et tirent les deltas via un curseur serveur. Un bootstrap snapshot évite de rejouer tout l'historique sur un nouvel appareil.

La Library expose un catalogue indépendant d'une université et versionne `cours → version → ressources`. Le manifeste indique les droits Premium et le hors-ligne ; les localisateurs de stockage objet restent internes au serveur.
