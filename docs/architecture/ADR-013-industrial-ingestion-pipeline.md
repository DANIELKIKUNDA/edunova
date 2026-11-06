# ADR-013 — Pipeline d'ingestion industriel séparé de l'API

## Décision
Les traitements documentaires longs sont exécutés dans un **worker dédié**. PostgreSQL porte l'état de la file. Chaque job possède un lease, un heartbeat, un nombre maximal d'essais et un état dead-letter.

## Raisons
- ne pas bloquer FastAPI pendant un OCR de centaines de pages ;
- permettre plusieurs workers horizontaux ;
- reprendre après crash sans double traitement ;
- conserver une vérité transactionnelle indépendante de Redis ;
- rester compatible avec le VPS initial et une montée en charge future.

## Sécurité
La chaîne applique préflight + antivirus avant staging. Les documents rejetés ne sont pas transformés. En production, l'absence de ClamAV est une erreur bloquante.

## Confidentialité
LOT 12 concerne les contenus préparés par l'équipe EduNova. Les documents personnels `deviceOnly` des étudiants restent en dehors de cette chaîne.

## Gouvernance
Aucun document ingéré n'est publié automatiquement. Le résultat est projeté dans EduNova Studio sous forme de brouillon et suit la gouvernance LOT 11.
