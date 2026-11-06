# EduNova v0.53.0 — Phase 18, lot 1 : coexistence Freemium/Premium/Campus

## Source de vérité consultée
- `docs/LOT5_FREEMIUM_POLICY.md` : accès gratuit local, Premium ≈ 1 USD/30 jours, IA et quotas configurables.
- `docs/architecture/ADR-049-commerce-campus-licensing-revenue-sharing.md` : licences Campus, sièges, Mobile Money, rapprochement, revenus partenaires.
- `services/api/app/modules/commerce/application/service.py` : abonnements individuels et règlement par webhook.

## Changements réels
- Nouvelle politique pure backend `combined_access.py` : 4 combinaisons d'accès, droits indépendants, expiration UTC, affiliation vérifiée, licence et siège obligatoires, suspension institutionnelle sans perte du Premium personnel.
- 14 tests backend ciblés exécutés et réussis.
- Modèle de lecture Flutter `combined_access.dart` et deux tests Flutter ajoutés (non exécutés ici faute de SDK).

## Limite explicite
Le modèle n'est PAS encore raccordé à une route API de lecture consolidée ni à une page Flutter. Aucun droit Campus n'est accordé par ce modèle seul : le backend doit vérifier l'affiliation, la licence et le siège dans leurs services de référence avant d'appeler la politique. Le lot 1 n'est pas une clôture de la Phase 18.
