# EDUNOVA v0.50.3 — Phase 15, confidentialité hiérarchique et lecture exécutive

Date : 14 octobre 2026. Statut : **checkpoint backend local PASS — Phase 15 EN COURS.**

## Point de départ canonique

- Source initiale vérifiée : `EduNova_v0.50.2_RC_PHASE15_SOURCE_LINEAGE_COMPLETENESS.zip`.
- Empreinte SHA-256 initiale recalculée : `4ee047cc659902fa3e4a9035453fbd8cb65ed84caa666f9e47899be0a3b36af3`.
- Régression d'entrée réellement exécutée : **816 passed in 103.38s (0:01:43)**, code de sortie 0.
- Roadmap inchangée ; aucun module universitaire antérieur n'a été reconstruit.

## Implémentation réelle

1. **Réduction des risques de divulgation par soustraction hiérarchique** : dans `services/api/app/modules/institutional_analytics/application/service.py`, une consultation gouvernée de cohorte, d'enseignement ou d'unité universitaire est supprimée lorsque la population distincte restante dans la période parente représente 1 ou 2 étudiants. La consultation de périmètres identiques ou laissant au moins 3 personnes dans le complément peut rester publiable si les autres contrôles sont respectés. L'écart se calcule sur des **étudiants distincts**, sans retour de liste nominative à l'API.
2. **Masquage cohérent** : en cas de risque de différence hiérarchique, masquage de chaque taux, dénominateur, couverture, empreinte de source et constat décisionnel ; suppression du nombre d'étudiants actifs exposé. Nouveau statut `suppressed_nested_difference`. Protection par défaut si la population parente est incohérente avec la population ciblée.
3. **Périmètre temporel** : pour un cours ou une cohorte sans période explicitement transmise, la période institutionnelle de l'objet autorisé est utilisée pour vérifier le complément, évitant d'intégrer les élèves d'années étrangères dans la décision de diffusion.
4. **Nouveau service de lecture exécutive** `executive_readout` : une vue descriptive de cinq métriques, état de qualité des sources, priorités nécessitant une revue humaine et conseils procéduraux, construite **uniquement à partir des données déjà filtrées** par `decision_brief`. Aucune décision académique, note, dossier individuel ou jury n'est modifié.
5. **Nouvelle route authentifiée** `GET /institutions/{iid}/intelligence/executive-readout` dans `services/api/app/modules/institutional_analytics/api/router.py`. Les autorisations institutionnelles, la restriction de faculté et l'isolation entre universités héritent des contrôles de `decision_brief`.
6. **Tests** `services/api/tests/test_phase15_hierarchical_privacy_executive.py` : onze nouveaux scénarios positifs/adversariaux couvrant le complément d'un ou deux étudiants, les membres inscrits plusieurs fois, les populations comparables, les périodes distinctes, les incohérences de sources, la protection de la vue exécutive, RBAC, facultés et multi-universités.

Aucune nouvelle table ni migration SQL n'est requise : dernière migration inchangée **0084**.

## Vérifications réellement exécutées

| Vérification | Résultat |
|---|---|
| Régression d'entrée v0.50.3 - 1 (v0.50.2) | 816 passed in 103.38s (0:01:43), exit 0 |
| Tests ciblés Phase 15 | 57 passed in 19.45s, exit 0 |
| Régression finale **après la dernière modification** | **827 passed in 104.38s (0:01:44), exit 0** |
| Audit `python scripts/audit_lot32_global.py` | **LOT32 GLOBAL AUDIT: 17/17 PASS, exit 0** |
| Vérification de syntaxe `python -m compileall -q services/api/app services/api/tests` | **PASS, exit 0** |
| Intégrité du ZIP et SHA-256 | Vérifiés au conditionnement, manifestes joints |

Commandes : `PYTHONPATH=services/api python -m pytest -q services/api/tests` ; tests d'intégration utilisant une base SQLAlchemy/SQLite de test.

## Limites et risques résiduels (ne pas surdéclarer la confidentialité)

- La suppression des *compléments hiérarchiques* concerne uniquement **les nouveaux points de consultation gouvernés de Phase 15** ; les tableaux historiques Lot 27, leurs exports, les éventuelles captures antérieures et les autres modules restent des surfaces distinctes à réexaminer.
- La protection ne garantit **ni l'anonymat, ni la confidentialité différentielle**. Les vues arbitrairement chevauchantes, les requêtes répétées avec évolution des inscriptions, les collusions et les inférences par métadonnées restent des risques. Aucun budget de requêtes durable, registre interrequêtes, ni traitement statistique garantissant une confidentialité formelle n'est implémenté.
- Les projections et effectifs sont lus par plusieurs requêtes SQL : aucune transaction intertables de snapshot cohérent global ni verrou PostgreSQL n'est revendiqué. Avant exposition publique, les conditions de concurrence devront être examinées sur infrastructure réelle.
- SHA-256 des indicateurs = empreinte descriptive du résultat diffusé, **ni signature numérique ni preuve d'immuabilité des données sources**.
- Les conseils aux gestionnaires restent des aides descriptives nécessitant validation humaine : pas de décision automatique, de recalcul des notes ou de certification du jury.
- Aucun Flutter build, base PostgreSQL réelle, Redis, stockage objet réel, appareil, fournisseur externe ou certification juridique n'a été exécuté ici.

## Décision

**EduNova v0.50.3 : checkpoint backend local vérifié. Phase 15 — EN COURS.**
La prochaine itération peut traiter les requêtes chevauchantes dans plusieurs unités/cohortes, l'audit des chemins hérités, la performance sur grands volumes et le contrôle de concurrence avant clôture de la Phase 15. Aucune Phase 16 engagée.
