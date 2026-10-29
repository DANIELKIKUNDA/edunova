# LOT 6 — Critères d'acceptation

## Backend
- [x] Question sur cours partagé sans preuve => abstention, 0 crédit.
- [x] Réponse sourcée => citations de pages.
- [x] Réponse commune en cache => 0 second crédit.
- [x] Document personnel => consentement obligatoire.
- [x] Document personnel => aucun cache partagé.
- [x] Politique production peut interdire totalement l'analyse distante personnelle.
- [x] SymPy résout les cas supportés à 0 crédit IA.
- [x] Échec fournisseur => crédit utilisateur libéré.
- [x] Échec fournisseur => budget global libéré.
- [x] Fallback => seul l'appel réussi est facturé.
- [x] Multi-fournisseurs configurable sans secrets dans le JSON.
- [x] Doublon fournisseur/modèle refusé.
- [x] Circuit breaker bloque les appels répétés vers un moteur défaillant.
- [x] Questions médicales => modèle haute fiabilité si disponible.
- [x] Conseil médical personnel => refus, 0 crédit.
- [x] Question médicale sans source => abstention.
- [x] Prompt injection dans un document => signal de sécurité.
- [x] Valeur numérique absente de la source => signal de sécurité.
- [x] Plafond IA quotidien => blocage avant dépense utilisateur.
- [x] Index partagé persistant.
- [x] Recherche PostgreSQL effectuée côté base avec FTS/Gin.
- [x] Migrations production versionnées 0001/0002/0003 et couverture complète des tables SQLAlchemy.

## Mobile
- [x] Écran assistant contextuel.
- [x] Historique local.
- [x] Consentement document personnel.
- [x] Citations cliquables vers le document personnel.
- [x] Affichage confiance/cache/crédits/signaux de sécurité.
- [x] Migration Drift v8 -> v9 écrite.
- [ ] `build_runner` sur SDK Flutter réel.
- [ ] `flutter analyze`.
- [ ] `flutter test`.
- [ ] build Android.
- [ ] build Web/PWA.
- [ ] build Windows.

## Production
- [ ] fournisseur(s) IA choisi(s) après benchmark qualité/coût ;
- [ ] `AI_DAILY_CREDIT_BUDGET` non nul et validé ;
- [ ] contrat confidentialité validé avant `AI_ALLOW_PERSONAL_DOCUMENTS=true` ;
- [ ] test réel Redis multi-worker ;
- [ ] métriques/coûts observés sur pilote.
