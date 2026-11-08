# EduNova v0.50.6 — Phase 15 : confidentialité temporelle des archives institutionnelles

**Date : 15 octobre 2026**  
**Base vérifiée :** `EduNova_v0.50.5_RC_PHASE15_LEGACY_ANALYTICS_PRIVACY_CLOSURE.zip`  
**SHA-256 recalculé :** `92e51581f06af42bad443e21c84bd6b80facdba41d6d5f26e34b4b4104832cc0`  
**Décision :** Phase 15 **OUVERTE**. Cette itération porte sur le backend local, pas la certification de production.

## Problème vérifié dans le code du checkpoint

La version v0.50.5 protégeait les consultations d'archives v3 contre les petites populations **actuelles**, mais elle ne liait pas une archive à la **composition exacte de la population au moment de sa capture**. Un groupe de cinq étudiants pouvait remplacer un membre par un autre tout en conservant le même effectif. Une archive ancienne restait alors publiable, malgré un risque d'inférence temporelle. De plus, les archives successives v3 pouvaient exposer simultanément les taux historiques et des différentiels.

## Correctifs effectivement codés

1. **Contrat d'archives v4, sans migration :** conservation en base d'une preuve de population d'étudiants actifs, distincts, filtrés par `institution_id`, période, unité, cohorte ou enseignement. La preuve est un **HMAC-SHA-256** calculé sur la population canonique et le périmètre, avec nonce aléatoire propre à chaque archive et secret de serveur. Les identifiants étudiants ne sont jamais placés dans le payload public.
2. **Vérification sur chaque lecture :** reconstitution de la preuve à partir de la population active actuelle. À effectif inchangé mais identité différente, l'archive est masquée (`capture_population_or_integrity_changed`). Les inscriptions étrangères/inactives n'affectent pas la preuve. Un secret absent ou renouvelé fait échouer la vérification de manière restrictive.
3. **Contrôle de l'intégrité :** le SHA-256 descriptif stocké est recalculé avant toute divulgation ; la preuve HMAC empêche qu'une simple réécriture de ce SHA-256 suffise pour falsifier la composition de la population. Ceci n'est **pas** une signature légale et ne prouve pas l'absence de toute compromission du serveur.
4. **Suppression des archives antérieures au contrat v4 :** les archives v1 à v3 restent stockées et restent listables comme métadonnées, mais leurs payloads et empreintes ne sont plus publiés. Les archives nouvellement créées sont au contrat v4.
5. **Différenciation temporelle :** au maximum **une archive v4 courante par liste autorisée** peut exposer son payload ; les archives plus anciennes exposent uniquement des métadonnées (`historical_temporal_suppressed`). Les comparaisons ne renvoient aucun delta lorsque les archives ne peuvent pas être publiées. Ce choix réduit expressément les fonctionnalités d'historique pour protéger les étudiants.
6. **Protection des métadonnées internes :** le nonce, le HMAC et l'indicateur d'intégrité ne sont pas renvoyés par la route de création, la route d'historique, ou les comparaisons.
7. **Continuité :** aucun gradebook, résultat officiel, décision du jury ou module de Phase 14 n'a été modifié. Les anciens chemins déjà filtrés en v0.50.5 restent gouvernés. Le fichier `app/version.py` a été synchronisé de sa valeur héritée `0.49.12` à `0.50.6`.

**Fichiers :**
- `services/api/app/modules/institutional_analytics/infrastructure/sqlalchemy_repo.py`
- `services/api/app/modules/institutional_analytics/application/service.py`
- `services/api/tests/test_phase15_temporal_archive_integrity.py` (nouveaux tests)
- `services/api/tests/test_phase15_legacy_surface_closure.py` (contrat v4)
- `services/api/tests/test_institutional_analytics_lot27.py` (nouveau nonce par capture)
- `services/api/app/version.py`, `.env.example`, `README.md`.

## Risques et limites documentés

- **Protection contre les requêtes répétées non exhaustive :** un utilisateur pouvant consulter des *dashboards vivants* à différentes dates pourrait encore inférer des variations ; une politique de budget de confidentialité persistant, une fenêtre de publication contrôlée ou un dispositif de differential privacy reste nécessaire. Il serait incorrect de déclarer le risque temporel définitivement éliminé.
- **Archives déjà divulguées :** le serveur ne peut pas retirer les copies préalablement téléchargées sous contrat v3.
- **Concurrence et isolation transactionnelle :** la preuve et les KPI sont obtenus par des requêtes distinctes ; des modifications simultanées peuvent produire une archive immédiatement invalidée. Un contrôle transactionnel et des tests PostgreSQL réels restent à faire aux phases prévues.
- **Gestion des clés :** `INSTITUTIONAL_ANALYTICS_HMAC_SECRET` peut être défini (32 caractères aléatoires minimum), sinon `JWT_SECRET` est utilisé. L'absence de clé refuse une nouvelle capture ; un changement de clé masque les archives signées avec l'ancienne, sans récupération automatique.
- **Performances :** la composition des populations est calculée à la capture et au contrôle d'archives ; les coûts SQL sur gros volumes ne sont pas certifiés dans cette itération.
- **Pédagogie historique :** l'ancienne agrégation pédagogique insuffisamment tracée reste masquée ; la lignée métier exhaustive n'est pas présentée comme résolue.
- **Audit statique :** le contrôle 17/17 prouve uniquement la présence de contrats structurels ; il ne remplace pas des tests de sécurité d'infrastructure.

## Vérifications

**Régression globale finale : 878/878 PASS (code 0 ; 152,44 secondes). Audit structurel : 17/17 PASS (code 0). Compilation Python : PASS (code 0).** Les résultats définitifs et codes de sortie sont consignés dans `TEST_EVIDENCE_PHASE15_v0.50.6.txt` après exécution intégrale. Tests incluant populations stables, changement d'identité à effectif constant, clés, falsification, lecture HTTP TestClient, RBAC et multi-tenant. Pas de Flutter, PostgreSQL, Redis, stockage objet ni appareils réels revendiqués.

## Décision

**Checkpoint backend v0.50.6. Phase 15 toujours EN COURS.** La clôture ne pourra pas revendiquer une résistance générale aux requêtes temporelles, à la collusion ni aux déductions à partir des anciens téléchargements.
