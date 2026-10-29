# ADR-0007 — Assistant RAG économique, sourcé et multi-fournisseurs

## Statut
Accepté — LOT 6 / v0.7.0

## Décision
EduNova ne dépend d'aucun fournisseur IA unique. L'assistant est construit autour d'un port `LlmProvider`, d'un catalogue de modèles et d'un routeur coût/qualité. En production, les fournisseurs sont chargés par configuration et les clés restent dans des variables d'environnement séparées.

Pour les cours partagés, l'assistant récupère d'abord des passages du cours et exige des preuves suffisantes avant tout appel au modèle. Les réponses sont accompagnées de citations de pages. En absence de preuve, EduNova s'abstient.

Pour les documents personnels, le fichier original reste local. Seuls quelques extraits sélectionnés localement peuvent être envoyés, après consentement explicite. Ces réponses ne sont jamais placées dans le cache partagé.

Les calculs scientifiques déterministes sont tentés avant l'IA via SymPy.

## Recherche
La baseline v0.7.0 utilise :
- PostgreSQL Full-Text Search français + index GIN pour les cours partagés en production ;
- fallback TF/IDF déterministe pour SQLite/tests ;
- port de récupération indépendant afin de permettre un retriever hybride pgvector plus tard sans toucher au domaine.

Le pgvector n'est volontairement pas figé avant le benchmark du modèle d'embeddings : la dimension, le coût et la politique de confidentialité dépendent du modèle choisi. Cette décision évite un verrouillage prématuré tout en gardant la frontière technique prête.

## Sécurité/coût
- quota utilisateur réservé avant appel ; validé uniquement après succès ; libéré en cas d'échec ;
- plafond global quotidien partagé via Redis en production ;
- fallback vers le modèle suivant uniquement après libération des réservations de l'appel échoué ;
- circuit breaker par fournisseur/modèle ;
- cache partagé uniquement pour les contenus communs ;
- refus du conseil médical personnel ;
- détection conservatrice de valeurs numériques absentes des sources ;
- aucune clé API dans l'application mobile.

## Conséquences
Le fournisseur, le modèle, le cache, le moteur de recherche et les politiques de coût peuvent évoluer sans modifier le domaine de l'assistant.
