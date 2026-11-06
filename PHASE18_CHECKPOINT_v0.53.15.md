# EduNova Phase 18 — v0.53.15 — intégration Campus payante

## Implémenté
- Commande Campus payante liée à une offre active/versionnée, avec capture des paramètres tarifaires.
- Paiement initialisé par le fournisseur configuré ; référence d'idempotence par établissement.
- Webhook signé : séparation des paiements Campus des achats Premium individuels.
- Validation serveur du montant, devise et fournisseur ; attribution de licence dans la même transaction SQL que le statut de commande/paiement.
- Double notification sans double prolongation ; paiement échoué sans activation ; suspension conservée (paiement en revue).
- API de lecture des commandes pour les administrateurs Campus ; catalogue public des offres actives.
- Interface Flutter : bouton de renouvellement, saisie Mobile Money, confirmation par vérification du statut serveur, jamais par confiance dans le client.
- Migration 0099 et tests métier réels.

## Tests réellement obtenus
- `pytest -q services/api/tests/test_phase18* services/api/tests/test_migration_contract.py` : 84/84 réussis.
- `compileall` du module commerce : réussi.
- Régression backend générale : tentée mais interrompue par délai d'exécution ; non certifiée.
- Flutter : compilation non exécutée, SDK absent.

## Limites bloquantes pour la production
- Le fournisseur sandbox est disponible en développement/test. Aucun fournisseur Mobile Money de production n'a été connecté ou certifié ici.
- Le parcours Flutter sélectionne pour le moment la première offre payante ; choix explicite des offres et moyens de paiement à enrichir.
- Remboursements et chargebacks après activation nécessitent une politique de suspension/revue financière, sans retrait automatique de l'historique.
- Concurrence PostgreSQL réelle, migrations sur environnement déployé, intégration opérateur et appareils réels restent à certifier.
- Le catalogue central Volcano Tech est déjà versionné dans la version précédente ; l'écran central de gestion des offres n'a pas été ajouté dans ce checkpoint.

Ne pas présenter ce checkpoint comme une clôture à 100 % de la Phase 18.
