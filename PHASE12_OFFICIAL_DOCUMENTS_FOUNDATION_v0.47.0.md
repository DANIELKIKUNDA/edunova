# EduNova v0.47.0 — Phase 12: fondation des documents officiels

## Implémenté et vérifié
- Réutilisation des demandes de la Phase 11 ; délivrance uniquement depuis une demande approuvée d'attestation, relevé ou duplicata.
- Génération effective d'un PDF (ReportLab), octets persistés, empreinte SHA-256 du PDF réellement produit.
- Numéro institutionnel unique, identifiant de document et jeton public aléatoire de vérification (seul son SHA-256 est persisté).
- Vérification publique minimisée : validité, état, numéro, type et empreinte ; pas de nom ni de matricule exposés.
- Révocation motivée et statut public immédiatement invalide.
- Délivrance et passage de la demande à FULFILLED avec événement dans une même transaction.
- Contrôle institutionnel et contrôle de lecture (étudiant concerné ou agent habilité), refus des doublons.
- Migration SQL 0072, contraintes d'unicité, index, API.

## Certification locale
- pytest : 592 tests PASS.
- contrat de migrations isolé : PASS.
- audit global LOT32 : 17/17 PASS.
- compileall : PASS.

## Limites importantes (non certifiées)
- Le PDF est un prototype institutionnel de référence, PAS un diplôme final ou un relevé détaillé officiellement validé.
- Les crédits, notes, décisions de jury, éligibilité à la diplomation et modèles institutionnels signés ne sont PAS encore générés à partir des sources canoniques.
- Pas de signature numérique institutionnelle, de certification W3C VC, ni de signature qualifiée.
- Le lien de vérification figure en texte ; QR graphique non encore intégré.
- Le document binaire est stocké en base pour cette fondation ; object storage chiffré, politiques de rétention, rotation de clés, protection contre l'énumération et exploitation de production restent à valider.
- Tests Flutter et PostgreSQL réel non exécutés.

## Références de conception
- W3C Verifiable Credentials Data Model 2.0 (recommandation mai 2025).
- 1EdTech Open Badges 3.0, signature et vérification des attestations.
Ces normes servent de cible d'interopérabilité et ne constituent pas une certification du module actuel.
