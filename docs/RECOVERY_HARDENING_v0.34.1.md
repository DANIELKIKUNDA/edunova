# EduNova v0.34.1 — Recovered Canonical Baseline Hardening

## But
Fermer les incohérences internes découvertes après la reconstruction v0.34.0, sans falsifier l'historique v0.33.2.

## Corrections
- audit LOT 32 rendu compatible avec une chaîne de migrations append-only au-delà de 0050 ; il exige désormais une chaîne contiguë jusqu'à la dernière migration et au minimum 0052 ;
- nom du test global de migration aligné sur la baseline récupérée ;
- version runtime de santé opérationnelle alignée sur 0.34.1 ;
- versions API, Flutter Student et Flutter Admin alignées sur 0.34.1 (+70 pour Flutter) ;
- README nettoyé de ses deux en-têtes de baseline contradictoires.

## Doctrine de certification
La certification ChatGPT couvre le code, les audits et les tests exécutables dans cet environnement. Flutter SDK/appareils, PostgreSQL/Redis de production, cloud, Mobile Money réel, charge, pentest externe et pilote humain restent OPEN dans leurs environnements respectifs.
