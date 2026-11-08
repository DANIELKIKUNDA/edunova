# Décision : audits cumulatifs et versions historiques

Les 17 échecs du 1 novembre 2026 ont été reproduits individuellement, avant
modification, dans `evidence/phase19-final/baseline/`. Les preuves de la première
certification sont conservées sans remplacement dans `evidence/local-phase19/`.

Les audits des lots 10 à 26 exigeaient simultanément des versions API allant de
0.12.1 à 0.27.2 et des versions mobiles différentes. Ces égalités ne peuvent pas
être vraies ensemble. Le fichier canonique `services/api/app/version.py` contient
0.52.7 ; FastAPI et `/health` utilisent maintenant cette même constante. Les
pubspecs déclarent mobile 0.53.0+18000 et admin 0.52.3+17003. Réintroduire des
chaînes anciennes dans les applications falsifierait les métadonnées.

Décision : pour les audits cumulatifs, une version historique est un minimum
numérique. Le helper vérifie aussi le branchement API et refuse les versions
absentes, invalides ou inférieures. Les vérifications métier de chaque script
restent obligatoires. Un minimum de version ne prouve aucune fonctionnalité.

| Audit | Cause reproduite | Contrat conservé / décision |
|---|---|---|
| lot10_uiux_maximal | version mobile 0.11.1 figée | minimum ; les 51 autres contrôles restent |
| lot11_maximal | API 0.12.1 figée | minimum et constante API câblée |
| lot12_ingestion | trois versions 0.13.1 figées | minimum ; sécurité ingestion inchangée |
| lot13_final | versions et libellé source | minimum ; page début/fin, citation et texte sélectionnable contrôlés |
| lot13_uiux_premium | trois versions 0.14.2 figées | minimum ; UI et gouvernance inchangées |
| lot14_final | trois versions 0.15.1 figées | minimum ; intégrité publication inchangée |
| lot15_final | versions et libellé exam | minimum ; carte Exam Mode, bouton Configurer et callback contrôlés |
| lot15_learning_experience | versions, seuil et libellés | minimum ; seuil courant 980, branche desktop/mobile et NavigationBar ; bascule Focus et sortie ; indication hors connexion |
| lot15_student_delight | trois versions 0.16.2 figées | minimum ; interactions inchangées |
| lot16_adaptive | API 0.17.0 figée | minimum ; routes et fichiers restent vérifiés |
| lot16_final | trois versions 0.17.1 figées | minimum ; sémantique de confiance inchangée |
| lot17_planner | API 0.18.1 figée | minimum ; capacité/ordre/verrouillage inchangés |
| lot21_tutor | API 0.22.0 figée | minimum ; route et gardes inchangées |
| lot22 | API 0.23.0 figée | minimum ; séparation tenant inchangée |
| lot22_deep | trois versions 0.23.1 figées | minimum ; rôles/FK/contraintes inchangés |
| lot26 | API 0.27.0 figée | minimum ; HMAC, TTL et unicité inchangés |
| lot26_closure | trois versions 0.27.2 figées | minimum ; workflows et routes inchangés |

Les libellés ont évolué dans les versions ultérieures documentées par les audits
lot13_uiux_premium et lot15_student_delight, déjà réussis hors versions. Le seuil
980 reste un choix de disposition et n'est pas un invariant de sécurité. Les
nouveaux critères vérifient plusieurs éléments structurels au lieu d'une seule
phrase. Ils ne remplacent ni les tests widget ni les tests métier.

Réserve réelle : StudyWorkspacePage et ExamSimulatorPage comportent encore des
données illustratives et callbacks vides. Le bouton de configuration Exam Mode
et l'indication offline ne prouvent donc pas un parcours connecté au backend.
Aucune nouvelle fonctionnalité n'est ajoutée pour masquer cette limite. Elle
interdit de conclure à une préparation complète à la production sur ces écrans.
