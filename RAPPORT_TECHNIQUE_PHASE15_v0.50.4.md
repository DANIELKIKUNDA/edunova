# EduNova v0.50.4 — Phase 15 : confidentialité des cohortes chevauchantes

**Date : 15 octobre 2026.**  **Statut : checkpoint backend local vérifié.**  Phase 15 **EN COURS** ; Phase 16 non engagée.

## Reprise canonique

- Point de départ : `EduNova_v0.50.3_RC_PHASE15_HIERARCHICAL_PRIVACY_EXECUTIVE.zip` ; ZIP source contrôlé ; SHA-256 source recalculé : `5624ac3fe1861fe78ed09c50fe955f210d925305b9971a2651fda46be3af0e35`.
- Code initial : **v0.50.3**, régression entrée **827/827 PASS** (`baseline_pytest.log`, `exit 0`). La roadmap 0–26 reste inchangée ; les phases antérieures restent conservées.
- Aucun module existant n'a été réécrit ; modifications locales dans le service et dépôt `institutional_analytics` ; tests adversariaux supplémentaires.

## Défaut corrigé : comparaison de cohortes partiellement chevauchantes

Le contrôle v0.50.3 empêchait les déductions lorsque la différence entre une cohorte et **tous** les étudiants de sa période était inférieure à trois personnes. Pourtant, deux **cohortes actives** d'une même période pouvaient partager quatre étudiants sur cinq tout en possédant chacune un complément institutionnel d'au moins trois étudiants. Les deux publications pouvaient contribuer à isoler une ou deux personnes.

La version **v0.50.4** ajoute un contrôle statique des **pairs** dans les consultations gouvernées `decision_brief` et, par héritage strict, `executive_readout` :

1. Recherche **uniquement dans la même université** et la **même période** des autres cohortes actives disposant d'un enseignement.
2. Calcul en SQL des populations **DISTINCT** et du recoupement avec le périmètre demandé. Les identifiants des étudiants ne sont **jamais renvoyés au service ou à l'API** ; seuls des décomptes agrégés sont utilisés.
3. Si un groupe de pair lui-même publiable diffère du public demandé par **un ou deux** étudiants (sur un côté au moins), toutes les métriques du périmètre demandé sont supprimées. Les cohortes identiques, disjointes, ou les groupes de moins de trois étudiants qui ne sont pas publiables, n'entraînent pas inutilement ce nouveau blocage.
4. Pour les vues d'unité, comparaison de l'audience totale avec ses cohortes membres et les autres cohortes publiables ; impossibilité de faire revivre des statistiques par la vue exécutive.
5. En cas de blocage, aucun taux, dénominateur, empreinte SHA-256 d'indicateur, pourcentage de couverture, effectif d'étudiants ou recommandation chiffrée n'est délivré : `overlapping_scope_suppressed` et `suppressed_overlapping_scope`.
6. La période est déduite d'un enseignement ou d'une cohorte lorsqu'elle n'est pas fournie explicitement, pour éviter un croisement avec les autres années universitaires.

Le calcul utilise un sous-ensemble de SQLAlchemy/SQL compatible avec SQLite de test. **Aucune nouvelle table ni migration** ; dernière migration existante **0084**.

## Tests nouveaux : 10 scénarios

- Deux cohortes de cinq inscrits ayant **quatre** étudiants communs (avec onze étudiants au niveau de la période) : blocage en vue cohorte **et** enseignement, y compris dans la vue exécutive.
- Deux cohortes avec **trois** inscrits communs sur cinq : blocage de la différence de deux.
- Cohortes identiques : statistiques toujours disponibles.
- Cohortes disjointes : statistiques toujours disponibles.
- Unité versus cohorte dont l'écart est une personne : blocage.
- Inscription d'une autre université insérée artificiellement : pas de contamination de la comparaison.
- Inscription inactive : non prise en compte dans les recoupements.
- Contrôles RBAC des étudiants, enseignants, acteurs étrangers ; validation des routes authentifiées.
- Période implicite d'un enseignement : mêmes protections.
- Cohorte pair de deux inscrits (déjà non publiable) : absence de surblocage.

## Vérifications **réellement exécutées**

| Contrôle | Résultat |
|---|---|
| Entrée canonique v0.50.3, suite globale | **827 passed in 68.85s**, exit **0** |
| Nouveaux tests dédiés après correction | **10 passed in 4.11s**, exit **0** |
| Tests Phase 15 après dernière modification | **67 passed in 13.17s**, exit **0** |
| Suite globale finale APRÈS toutes les modifications | **837 passed in 66.86s**, exit **0** |
| Audit `python scripts/audit_lot32_global.py` | **17/17 PASS**, exit **0** |
| `python -m compileall -q services/api/app services/api/tests` | PASS, exit **0** |
| ZIP final et manifestes SHA-256 | Vérifications effectuées au conditionnement |

Commande de régression : `PYTHONPATH=services/api python -m pytest -q services/api/tests`.
Les tests utilisent des dépôts SQLAlchemy/SQLite de test (pas PostgreSQL réel).

Une assertion intermédiaire de test basée sur la recherche de la séquence « b1 » dans un UUID aléatoire a échoué (faux positif). Le contrôle a été corrigé pour rechercher une valeur JSON complète ; les **10 tests dédiés**, les **67 tests ciblés** et les **837 tests finaux** ont ensuite tous réussi. Le code métier n'a pas été modifié pour masquer cet échec de test.

## Périmètre non certifié / limites importantes

- La suppression concerne les **points de consultation gouvernés de Phase 15** ; les tableaux anciens (Lot 27), `dashboard`, `executive_report`, snapshots et exports historiques sont toujours des voies séparées **à auditer** avant une garantie globale de confidentialité.
- Ce garde couvre les pairs **cohortes** actifs connus du système ; il ne couvre pas toutes les unions d'unités ni les **combinaisons arbitraires** de filtres, consultations répétées, collusions, modifications d'inscriptions entre requêtes ou inférences externes. Pas de confidentialité différentielle formelle ni de budget de consultation persisté.
- Les statistiques et effectifs sont lus par plusieurs requêtes ; l'isolation transactionnelle PostgreSQL et les courses concurrentes doivent être certifiées sur la machine. Des validations de montée en charge restent nécessaires.
- Les empreintes SHA-256 sont descriptives, ni signature électronique ni preuve indépendante d'immuabilité.
- Aucune compilation Flutter, base PostgreSQL/Redis réels, stockage objet, appareil réel ou fournisseur externe n'a été exécuté pendant cette itération.
- Aucune modification des notes officielles, bulletins, délibérations ou dossiers Student Success ; décisions toujours humaines.

## Décision

**Checkpoint backend local accepté : EduNova v0.50.4, Phase 15 toujours EN COURS.**
Suite prioritaire : audit des anciens tableaux et exports permettant potentiellement le contournement des contrôles nouveaux, cohérence transactionnelle et performances sous volumétrie réelle. Ne pas passer à la Phase 16 avant consolidation documentée.
