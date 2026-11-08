# ADR-0005 — Commerce indépendant des stores et Mobile Money

## Décision
EduNova attache Premium au **compte EduNova**, jamais à un appareil ni à un store. Le canal commercial principal en RDC est le Mobile Money intégré dans EduNova (PWA et APK direct). Google Play/App Store restent des canaux de distribution optionnels soumis à leurs règles propres.

## Conséquences
- backend seul autoritaire pour l'activation Premium ;
- confirmation exclusivement après callback/webhook fournisseur vérifié ;
- `Idempotency-Key` obligatoire au checkout ;
- aucun secret fournisseur dans Flutter ;
- les adaptateurs Mobile Money sont interchangeables derrière un port ;
- le sandbox est interdit en production ;
- un compte Premium reste Premium sur tout appareil connecté au même compte.
