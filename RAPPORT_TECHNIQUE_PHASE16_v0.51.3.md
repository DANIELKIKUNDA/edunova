# EduNova v0.51.3 — Phase 16 : politiques de bibliothèque par université

## Origine certifiable
- Checkpoint source : `EduNova_v0.51.2_RC_PHASE16_LIBRARY_CIRCULATION_GOVERNANCE.zip`.
- SHA-256 vérifié avant extraction : `eed0a0e201a47ff2669fed0ef9b79e0707f9375d77faec622af882480e28a52e`.
- La roadmap 0–26 est inchangée, modules préexistants préservés. **Phase 16 toujours ouverte**.

## Développements backend réels
- Politique de circulation configurable **par université** : durée d'emprunt 1–60 jours, quota simultané 1–10, renouvellements 0–2, durée de renouvellement 1–30 jours.
- Conserve les paramètres par défaut **21 jours / 3 prêts / 2 prolongations de 14 jours** lorsqu'aucune configuration n'est enregistrée ; lecture sans création implicite de ligne.
- Migration `0089_campus_library_tenant_policy_v0_51_3.sql` créant la table `campus_library_policies` avec contraintes CHECK et `row_version` ; ORM correspondant.
- API authentifiée `GET /v1/campus-services/institutions/{institution_id}/library/policy` pour un membre actif et `PUT` réservé aux administrateurs institutionnels autorisés.
- Mise à jour optimiste `expected_version`: `0` pour premier enregistrement, versions strictement croissantes ensuite ; échec des versions périmées (HTTP 409). Contrôle des paramètres côté Pydantic, service et SQL.
- Les emprunts lisent et appliquent le quota et la durée **dans la transaction de création** ; les renouvellements relisent les paramètres effectifs dans leur transaction. Verrou consultatif PostgreSQL par tenant pour sérialiser modifications des règles et opérations de prêt, conservant le verrou par emprunteur et l'index d'unicité des prêts actifs.
- Les échéances des prêts déjà accordés **ne sont pas modifiées rétroactivement**. Les futures prolongations suivent les règles applicables à leur moment.
- Journal d'audit sur mise à jour réussie. Ni le gradebook, ni les notes officielles, ni les finances ne sont touchés.

## Frontend Flutter implémenté (compilation non exécutée)
- Le gateway campus existant utilise GET/PUT authentifiés, `Cache-Control: no-store`, identité de l'université validée, payload versionné.
- L'écran `Bibliothèque physique` charge et affiche le règlement réel de l'université, et propose un formulaire de modification aux seuls rôles administratifs visibles. Validation des bornes et message contextualisé en cas de conflit de version.
- Le changement d'université vide les paramètres en mémoire, vérifie le contexte de la boîte de dialogue et rejette une réponse ancienne. La règle affichée pour la prolongation est dynamique.
- Deux scénarios de tests Flutter **écrits mais non exécutés** dans le test du gateway (lecture/écriture CAS, ID/tenant malformé).

## Preuves exécutées localement
- Cible Phase 16 + migrations + contrat version : **55/55 PASS**, `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_phase16_library_tenant_policy_v0_51_3.py services/api/tests/test_phase16_library_governance_v0_51_2.py services/api/tests/test_phase16_physical_library_v0_51_1.py services/api/tests/test_migration_contract.py services/api/tests/test_release_version_contract.py`.
- **Régression backend globale finale : 965/965 PASS**, code retour `0`, commande `PYTHONPATH=services/api python -m pytest -q services/api/tests`; voir `REGRESSION_BACKEND_v0.51.3.txt` (copie du journal complet).
- `python -m compileall -q services/api/app` : **PASS**.
- Audits structurels de câblage **16/16**, **20/20** et **18/18 PASS** ; ces scripts lisent les sources et ne compilent pas Flutter.
- Tests positifs et adversariaux ajoutés : paramètres hors bornes, quota personnalisé, absence de politique, anciennes échéances immuables, changement de règlement, CAS/rejeu, accès étudiant/auditeur/faculté, université étrangère, institution suspendue, contraintes SQL, contrats HTTP, audit.
- Une tentative de régression de référence a dépassé le délai du shell et a été interrompue. **Elle n'est pas comptée comme réussite.** La preuve de validation est uniquement la régression finale intégrale passée avec code 0.

## Certifications NON exécutées, limites documentées
- Absence de SDK Flutter/Dart : **aucun** `flutter analyze`, `flutter test` ou `flutter build` exécuté. La syntaxe et le fonctionnement des nouvelles interfaces doivent être vérifiés sur une machine équipée ; la Phase 23 reste consacrée aux appareils physiques.
- La migration **0089 non appliquée sur PostgreSQL réel**, et les verrous consultatifs en situation multiprocessus **non certifiés**. Les tests des services sont réalisés avec SQLite.
- Redis, stockage objet, prestataires externes et performances à l'échelle ne sont pas certifiés.
- Périmètre restant Phase 16 : pertes et dommages aux exemplaires, notifications, inventaire et maintenance, intégration ressources/horaires, événements universitaires et Alumni, pagination/recherche des grands catalogues.
- La mise à jour de politique est transactionnelle dans sa base ; le journal d'audit reste opéré par le composant d'audit existant après succès, sans affirmer une atomicité transversale qu'aucun test ne démontre.

**Décision : nouveau checkpoint canonique backend local v0.51.3 ; frontend développé mais non certifié Flutter ; Phase 16 en cours.**
