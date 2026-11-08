# EduNova v0.53.8 — Frontière de paiement des renouvellements Campus

## Audit et correction
La route `POST /campus/{institution_id}/licenses/renew` acceptait un `renewal_reference` fourni par le client, ainsi qu'un `price_cdf > 0`, et provisionnait immédiatement une licence. La référence n'était **pas** une preuve de paiement vérifiée. Désormais, les renouvellements payants sont refusés par HTTP 409 `verified_payment_required_for_paid_campus_renewal` **avant toute mutation**. Les renouvellements administratifs à prix zéro restent possibles sous les permissions existantes.

## Limites importantes
Il ne s'agit pas encore de la liaison complète Mobile Money → Campus : aucun nouveau flux de règlement institutionnel n'a été implémenté. Les services internes `renew_license` et l'ancienne route de création de licence demandent une revue des privilèges et de la preuve de paiement avant exposition commerciale. Ne pas considérer les licences administratives comme des reçus Mobile Money. Flutter non compilé ici. Régression globale non exécutée sur ce lot.

## Validation
`PYTHONPATH=services/api python -m pytest -q services/api/tests/test_phase18_paid_renewal_boundary.py services/api/tests/test_phase18_campus_renewal.py` : 15 passed.
