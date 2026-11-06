# EduNova v0.53.6 — Phase 18 / Renouvellement administratif Campus

- Nouvel endpoint authentifié `POST /v1/commerce/campus/{institution_id}/licenses/renew` (préfixe du routeur à vérifier selon montage).
- Référence de renouvellement stable, UUID déterministe, déduplication transactionnelle et refus d'une même référence avec paramètres contradictoires.
- Continuité à partir de la fin de période payée, sans additionner le délai de grâce; licence suspendue ou annulée non réactivée automatiquement.
- Journal commercial ajouté dans la même transaction que la licence; **aucun paiement Mobile Money n'est initié ni vérifié par cette opération administrative**.
- Contrôle RBAC institutionnel conservé.
- Tests ciblés: 62 réussis. Pas de compilation Flutter ni de régression backend générale dans ce lot.
- Travail restant: intégration avec preuve de paiement et gouvernance Volcano Tech, flux Flutter de renouvellement, tests sur appareils.
