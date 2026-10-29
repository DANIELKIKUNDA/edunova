# EduNova v0.50.2 — Phase 15, traçabilité et fiabilité des sources institutionnelles

Date : **14 octobre 2026**. État : **développement backend local vérifié ; Phase 15 toujours ouverte**.

## Reprise exacte

- Checkpoint canonique initial : `EduNova_v0.50.1_RC_PHASE15_PERIOD_COMPARABILITY_INTEGRITY.zip`.
- SHA-256 initial recalculé : `d9a2d885978720c87038596376c880c4bc79caae27ea1bb3206a0a77c62c2eb2` (conforme au fichier fourni).
- Tests backend initiaux sur la base v0.50.1, terminés avec code de sortie **0** : **796/796 PASS**.
- Aucun nouveau schéma ou migration SQL : dernière migration conservée `0084_assessment_grading_snapshot_v0_49_12.sql`.
- Les phases 0 à 14 et les modules historiques sont préservés ; les projections historiques de Lot 27 conservent leur sémantique distincte des agrégats gouvernés de Phase 15.

## Modifications réelles du code

1. **Provenance statistique et définition versionnée** dans `services/api/app/modules/institutional_analytics/application/service.py` : contrat de source explicite et version de lignée **2** pour chaque indicateur institutionnel gouverné. Une empreinte SHA-256 du **résultat agrégé publiable**, de son contexte institutionnel et de son contrat est fournie seulement après validation du seuil de divulgation. Cette empreinte **n'est ni la preuve cryptographique des données brutes, ni une signature électronique, ni une attestation immuable**.
2. **Mesure prudente de couverture observée**, sans identifiants personnels dans l'API : pour les présences et le gradebook, proportion d'étudiants actifs distincts disposant d'au moins une observation admissible, publiée seulement si l'indicateur est lui-même publiable. Cette mesure de « reach » **n'est pas la complétude de tous les événements attendus**.
3. **Comparaisons entre périodes plus strictes** : pour les taux de présence et de réussite, comparaison uniquement si l'observation touche au moins **80 %** des inscrits actifs dans **les deux périodes**, en sus des protections préexistantes (au moins cinq étudiants par période, populations disjointes, RBAC, périmètre, contrat de définition identique). Ce seuil de 80 % est un choix de politique conservateur, **pas** une garantie statistique d'absence de biais.
4. **Alertes non trompeuses** : les observations partielles restent affichées comme descriptions admissibles, mais ne génèrent pas de nouvelles alertes institutionnelles automatiques si la couverture de population est trop faible.
5. **Intégrité des notes exploitées pour la décision** dans `services/api/app/modules/institutional_analytics/infrastructure/sqlalchemy_repo.py` : contrôle des barèmes pondérés (100 %, maximums positifs, seuil de réussite raisonnable), notes admissibles, références de composants, doublons de lignes et bulletins publiés sans composants. Les notes publiées contradictoires ne peuvent pas être présentées comme des taux institutionnels fiables. Les notes officielles et les décisions du jury ne sont jamais modifiées.
6. **Intégrité des présences** : les statuts incohérents dans les présences clôturées / non contestées invalident la publication du taux gouverné, au lieu de fausser le dénominateur.
7. **Éviter la rupture rétrocompatible** : les calculs historiques non gouvernés (Lot 27) continuent à employer leur chemin existant, le nouveau contrat étant limité au tableau de décision de Phase 15.

## Tests et audits effectués

| Vérification | Résultat réel |
|---|---|
| Régression complète sur la base d'entrée v0.50.1 | **796/796 PASS**, code 0 |
| Nouveaux tests SQLAlchemy/SQLite de cette étape | **20 nouveaux cas**, positifs et adversariaux |
| Tests ciblés Phase 15 après dernière modification | **46/46 PASS**, code 0 |
| Régression finale **après la dernière modification** | **816/816 PASS**, code 0, **63,22 s** |
| `python scripts/audit_lot32_global.py` | **17/17 PASS**, code 0 |
| `python -m compileall -q services/api/app services/api/tests` | **PASS**, code 0 |
| Archive canonique | Vérification ZIP et SHA-256 par fichier joint |

La dernière régression a été lancée en tâche d'arrière-plan avec sa sortie dans un fichier et son code de sortie attesté après terminaison ; aucun timeout ne constitue une preuve PASS. Les tests nouveaux utilisent la vraie couche SQLAlchemy avec **SQLite de test**, et non un PostgreSQL de production.

Tests adversariaux : barèmes qui ne totalisent pas 100 %, notes négatives ou supérieures au barème, maximum nul, seuil invalide, bulletins publiés sans composants, statuts de présence falsifiés, provenance interne absente, contributeurs trop peu nombreux, évaluation d'une population partiellement observée, RBAC et isolation entre universités. Tests positifs : intégrité du calcul des ratios, fingerprint déterministe et sensible aux changements de métrique/périmètre, comparaisons de cohortes complètes et disjointes, conservation des notes.

## Limites explicitement maintenues

- Pas de compilation Flutter, certification sur appareil, PostgreSQL réel, Redis réel, stockage objet réel ou fournisseur externe ; ces contrôles restent affectés aux phases de certification machine et de fournisseurs.
- Les empreintes concernent seulement les statistiques diffusables calculées à la demande. Aucune chaîne d'audit signée, transaction de lecture à instantané unique sur plusieurs tables, ni ancrage immutable des lignes sources n'est prétendu.
- Couverture de population et taux observé ne démontrent ni l'exhaustivité de toutes les séances, ni celle des évaluations attendues ; les données historiques peuvent rester insuffisantes.
- Le filtre de groupes disjoints et les seuils de divulgation **ne résolvent pas** les attaques par requêtes répétées ou agrégats imbriqués : aucun budget de confidentialité persisté, confidentialité différentielle, ni contrôle automatique interrequêtes n'est revendiqué.
- Les comparaisons sont **descriptives**, non causales, et ne peuvent pas prononcer de décisions universitaires, recalculer les notes officielles ou modifier le jury.

## Décision

Checkpoint **v0.50.2 vérifié au niveau backend local**. **Phase 15 — Intelligence institutionnelle : EN COURS**. Les approfondissements ultérieurs doivent continuer à partir de ce ZIP, notamment la confidentialité interrequêtes, une attestation plus complète des sources et l'expérience exécutive sans reconstruire les modules existants.
