# EduNova v0.49.10 — Phase 14 : chronologie des tentatives et intégrité des notes

**Continuité :** `EduNova_v0.49.9_RC_PHASE14_IDENTITY_PROVENANCE.zip` (SHA-256 source vérifié : `c4864bbc866963ed8978d78e0d059971dbd8ec59c43f213406f70482052b11dc`). Phases 0 à 13 conservées, Phase 14 toujours ouverte. Aucun module recréé.

## Failles fonctionnelles constatées dans le code réel

La projection pédagogique v0.49.9 sélectionnait une reprise par `submitted_at`, avec repli sur `started_at`. En présence d'une nouvelle tentative commencée après l'ancienne, mais dont la date de soumission est rétrodatée ou corrompue, l'ancienne copie pouvait redevenir la source analytique (résurrection d'une preuve caduque). En outre, les détails `assessment_results.questions` étaient analysés sans valider la cohérence numérique minimale des champs agrégés (`earned`, `possible`, `percent`, `passed`) du même résultat.

## Implémentation ciblée

- **Reprises :** ordre de priorité par `started_at` (puis soumission et ID comme départage déterministe) pour chaque `(account_id, blueprint_id)`. Une reprise sélectionnée invalidée ne déclenche **aucun repli** sur les résultats d'une copie précédente.
- **Chronologie :** `submitted_at` doit exister et être postérieur ou égal à `started_at`. Conversion explicite des datetimes PostgreSQL avec fuseau et SQLite local sans fuseau vers UTC ; un horodatage impossible exclut l'analyse, sans réécriture de la note officielle.
- **Total noté :** avant de lire les détails par question, `earned`, `possible`, `percent` doivent être finis et numériques ; `0 ≤ earned ≤ possible`, `possible > 0`, `0 ≤ percent ≤ 100`, `passed ∈ {0,1}` ; le pourcentage doit correspondre aux points à ±1 point (tolérance d'arrondi).
- **Deux parcours :** les contrôles identiques s'appliquent à `objective_signals` ET `objective_trends`, y compris aux erreurs récurrentes. Les cellules de moins de trois étudiants évalués restent masquées.
- **Protection institutionnelle :** les filtres existants tenant/offering et la liste de comptes actifs sont conservés avant la sélection des tentatives, aucune donnée individuelle ajoutée à la réponse, aucun effet sur gradebook/jury.

## Vérifications adversariales ajoutées

1. Nouvelle reprise antidatée non autorisée à réactiver une ancienne note (signal et tendance).
2. Reprise commencée le plus récemment choisie même si l'ancienne copie a été soumise plus tard.
3. Série paramétrée d'agrégats impossibles (points négatifs, plus de points acquis que possibles, division par zéro, pourcentage incohérent ou hors bornes, verdict invalide) : aucune preuve exploitable.
4. Valeurs NaN/Inf : contrôle unitaire direct, car SQLite peut normaliser NaN vers NULL et rendre le scénario SQL non représentable.
5. Arrondi légitime `1/3 → 33 %` accepté : protection contre un durcissement excessif.

## Décisions de périmètre

- Le schéma existant demeure inchangé (dernière migration SQL `0082_pedagogical_objective_evidence_v0_49_2.sql`), aucune migration ajoutée.
- Les résultats d'anciennes tentatives peuvent contenir des détails de question partiels ; on ne prétend pas vérifier l'égalité des sommes des questions avec les totaux de note, car le modèle historique ne garantit pas cette exhaustivité. Cette limite reste à traiter à la source avec un contrat versionné, plutôt qu'en inventant des données.
- Aucun changement d'API, de rôle institutionnel ou de logique de notation; analyse en lecture seule et sans diagnostic individuel, sans modèle prédictif.
- Les résultats de tests et bornes précises de certification sont archivés dans `docs/certification/PHASE14_ATTEMPT_RESULT_INTEGRITY_v0.49.10_TEST_EVIDENCE.txt`.
- La compilation Flutter, les dispositifs physiques, PostgreSQL/Redis/object storage **réels** et fournisseurs tiers ne sont pas certifiés ici.

**Statut :** Phase 14 continue, Phase 15 non lancée, freeze v1.0 non prononcé.
