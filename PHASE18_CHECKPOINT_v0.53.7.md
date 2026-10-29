# EduNova v0.53.7 — Phase 18 / Renouvellement : références strictes

- Audit du renouvellement Campus v0.53.6 et de son journal commercial.
- Rejet des références de renouvellement vides, avec espaces en début/fin ou caractères de contrôle (tabulation, saut de ligne, NUL, DEL). Empêche les références visuellement ambiguës.
- Rejet des codes de plan avec espaces périphériques.
- Tests supplémentaires pour références ambiguës et codes de plan.
- ATTENTION : le renouvellement administratif continue à provisionner des droits **sans preuve de paiement Mobile Money**. Ne pas exposer ce flux comme un achat ou une activation payée en production ; revoir le périmètre d'autorisation avant déploiement.
- Tests Flutter et intégration Mobile Money réel non certifiés.

Résultat de tests : voir /mnt/data/phase18_0537_tests.log (exécution ciblée).
