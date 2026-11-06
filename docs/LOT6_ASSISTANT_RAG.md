# LOT 6 — Assistant intelligent, RAG et routeur IA économique

## Objectif
Transformer EduNova en tuteur contextuel fiable, capable d'expliquer les cours, de simplifier, comparer, tester, vérifier et résoudre certains exercices, tout en protégeant la confidentialité et le budget d'exploitation.

## Capacités livrées

### 1. RAG sourcé
- index persistant des chunks des cours partagés ;
- recherche PostgreSQL Full-Text Search français en production ;
- sélection bornée des meilleurs passages ;
- citations vers pages/sections ;
- score de confiance basé sur l'évidence ;
- abstention si aucune preuve ou preuve trop faible.

### 2. Documents personnels
- PDF original non téléversé par défaut ;
- sélection locale de quelques extraits ;
- consentement explicite avant analyse distante ;
- limite de taille côté API ;
- aucune insertion dans l'index de connaissances partagé ;
- aucun cache partagé ;
- historique de conversation conservé localement sur l'appareil.

### 3. Assistant contextuel
Modes :
- expliquer ;
- simplifier ;
- comparer ;
- me tester ;
- vérifier une réponse ;
- résoudre un exercice scientifique ;
- tutorat général lorsque la politique le permet.

### 4. Sciences quantitatives
SymPy est interrogé avant tout modèle génératif pour les équations simples supportées. Une solution déterministe coûte 0 crédit IA.

### 5. Routeur économique multi-fournisseurs
- modèles décrits par qualité, coût abstrait, contexte et capacités ;
- coût-first sous contrainte de qualité ;
- haute fiabilité exigée pour les questions médicales ;
- fallback vers un modèle compatible ;
- circuit breaker par fournisseur/modèle ;
- configuration multi-fournisseurs via `AI_PROVIDERS_JSON` ;
- secrets injectés séparément par variables d'environnement.

### 6. Maîtrise des dépenses
- réservation atomique du quota IA utilisateur ;
- commit après succès ; release après échec ;
- portefeuille inclus + crédits achetés déjà séparés par LOT 5 ;
- plafond global quotidien partagé par Redis ;
- production bloquée par défaut si `AI_DAILY_CREDIT_BUDGET=0` ;
- cache 7 jours pour les réponses communes sourcées ;
- lecture d'une réponse en cache : 0 crédit.

### 7. Sécurité pédagogique
- détection d'instructions hostiles incluses dans les documents ;
- le texte source est traité comme donnée, jamais comme instruction système ;
- refus du diagnostic/traitement médical personnel ;
- une question médicale sans source s'abstient ;
- valeurs numériques introduites sans preuve signalées et confiance abaissée.

### 8. Mobile/offline
- conversations stockées localement ;
- citations cliquables ;
- indicateur cache/confiance/crédits ;
- consentement visible sur les documents personnels ;
- Drift v9 : messages enrichis avec `abstained`, `cacheHit`, `safetyFlagsJson`, `routeReason`.

## Hors périmètre volontaire de fermeture
- choix du fournisseur IA production ;
- prix réel des crédits supplémentaires ;
- benchmark d'embeddings et activation pgvector hybride ;
- certification Flutter sur SDK réel ;
- certification confidentialité contractuelle d'un fournisseur pour les documents personnels.

Ces points sont des décisions de déploiement/benchmark, pas des dépendances cachées du domaine.
