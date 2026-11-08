# EduNova v0.53.12 — sécurité du service commercial

## Correction
Les protections des licences Campus payantes s’appliquent désormais aussi dans CommercialService.create_license et CommercialService.renew_license, pas uniquement dans les routes HTTP. Tout prix non nul est refusé sans parcours de paiement vérifié. Aucun flux de paiement Campus vérifié n’est encore intégré.

## Validation
30 tests ciblés réussis (commerce historique, renouvellements, garde API et garde service). Régression backend complète lancée, mais interrompue par le délai d’exécution; ne pas la considérer validée. Flutter non compilé.

## Reste à faire
Paiement Campus confirmé et provisionnement transactionnel; catalogue centralisé des offres; Flutter paiements Campus; certification générale. Phase 18 non clôturée.
