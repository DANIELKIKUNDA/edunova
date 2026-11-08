# ADR-0002 — Traitement des documents personnels

## Décision

Le fichier personnel reste sur l'appareil par défaut. Deux modes sont exposés au domaine :

- `deviceOnly` : aucun texte ni binaire n'est envoyé au serveur ;
- `onlineAssist` : l'utilisateur consent explicitement à l'envoi temporaire des extraits nécessaires à une opération IA.

## Conséquences

- aucune analyse distante implicite ;
- aucune sauvegarde cloud automatique du document personnel ;
- les ressources EduNova partagées peuvent être prétraitées côté serveur ;
- les adaptateurs OCR/extraction doivent être spécifiques aux plateformes tout en respectant le même port applicatif ;
- la perte d'un appareil peut entraîner la perte des documents locaux tant qu'une sauvegarde cloud facultative n'existe pas.
