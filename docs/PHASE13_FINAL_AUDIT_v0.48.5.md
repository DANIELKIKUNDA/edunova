# EduNova v0.48.5 — Phase 13, audit final de comparabilité

## Défaut corrigé
Les réévaluations de Student Success pouvaient produire `stable` lorsqu'aucune dimension ne disposait d'éléments comparables entre deux observations (absence de résultats publiés et moins de trois présences clôturées). Ce résultat aurait été interprétable à tort comme une stabilité académique prouvée.

Le moteur renvoie désormais `insufficient` lorsque les observations ne permettent aucune comparaison valide. Une première mesure fondée uniquement sur une ou deux présences est également `insufficient`. Les évaluations possédant une dimension réellement comparable continuent d'utiliser les règles existantes.

## Vérifications exécutées
- Suite complète : **621 passed** (29.56s), exit code 0.
- Tests Student Success ciblés : **14 passed**.
- Contrat de migration et module global LOT32 : **7 passed**.
- `python -m compileall -q services/api/app` : **PASS**.
- Migration inchangée, dernière **0081**.

## Limites
Ces tests ne démontrent pas une mesure causale de l'efficacité des interventions, ni la comparabilité temporelle de cohortes, ni le comportement sur Flutter, appareils réels, PostgreSQL de production ou intégrations externes. Une revue RBAC des rôles d'enseignants et des données de suivi sensibles reste recommandée lors de la phase sécurité. Le moteur n'est pas un dispositif de diagnostic médical ou psychologique.
