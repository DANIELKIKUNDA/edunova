# EduNova v0.48.0 — Phase 13 : Student Success Foundation

## Périmètre livré
Registre institutionnel des situations de suivi étudiant : création par un agent autorisé, catégories academic/attendance/engagement/wellbeing/other, priorité descriptive, affectation à un agent autorisé, cycle open → in_progress → resolved → closed (avec réouverture de resolved), journal d'événements atomique et versionnement optimiste. API `/v1/student-success/institutions/{iid}/cases` et variantes get/list/transition/timeline. Le dossier étudiant et les memberships Campus canoniques sont réutilisés ; isolation institutionnelle et lecture personnelle étudiante sont contrôlées.

## Limitations et sécurité
Aucun modèle prédictif, score de décrochage, diagnostic médical ou traitement automatique de décision n'a été ajouté. La priorité est déclarative et humaine, non statistique. Le suivi doit éviter toute donnée médicale sensible dans les notes libres ; la gouvernance détaillée, la minimisation et les politiques de conservation restent à approfondir. Les évaluations automatisées, l'agrégation de signaux de notes/présences et les notifications ne sont pas incluses. La certification Flutter et PostgreSQL réel n'est pas couverte.

## Certification locale
- 610 tests backend PASS (suite complète).
- 4 tests ciblés PASS, dont 3 nouveaux tests Student Success et contrat de migrations.
- Migration 0078, deux tables student_success_cases et student_success_events.
- Le module ne remplace ni le gradebook, ni les dossiers étudiants, ni le guichet.
