# EduNova v0.34.0 — Recovered Canonical Baseline

## Origine
Reconstruction contrôlée depuis `EduNova_v0.33.3_RC_Official_Brand_Integration.zip` (baseline physique survivante). La v0.33.2 annoncée précédemment n'était plus disponible comme artefact source vérifiable; elle n'est donc pas falsifiée ni recréée sous le même numéro.

## Delta récupéré
- gouvernance plateforme Volcano Tech distincte de Campus et Studio;
- 7 rôles: Owner, Platform Administrator, Finance/Commercial, Content/Editorial, Support Operator, Security/Audit, Read-only Analyst;
- permissions explicites et principe du moindre privilège;
- attribution/révocation auditée, verrouillage optimiste et interdiction d'auto-désactivation Owner;
- dashboard contractuel spécifique à chaque rôle;
- migrations PostgreSQL 0051 et 0052;
- endpoint `/v1/platform/*`;
- branding officiel conservé; splash mobile utilise désormais l'asset officiel et la signature From Volcano Tech;
- démarrage secondaire non bloquant conservé (sync/notifications/push ne bloquent pas le shell).

## Certification ChatGPT
- baseline survivante avant reconstruction: 471/471 tests backend PASS;
- baseline récupérée: 476/476 tests backend PASS;
- migrations: 0001..0052 contiguës;
- compileall backend: PASS;
- Flutter SDK/appareils réels: OPEN-machine / OPEN-device.

## Frontière de vérité
Cette version est une nouvelle baseline de récupération. Elle ne prétend pas être l'artefact historique v0.33.2. Les certifications Flutter, appareils, cloud, fournisseur Mobile Money, charge et sécurité externe restent ouvertes dans leurs environnements réels.
