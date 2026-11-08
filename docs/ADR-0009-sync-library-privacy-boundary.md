# ADR-0009 — Synchronisation cloud, bibliothèque commune et frontière privée

## Décision
EduNova sépare strictement trois classes de données.

1. **Local-only** : PDF/images personnels, texte OCR personnel, chunks personnels, annotations privées et conversations assistant liées aux documents personnels. Ces données ne sont jamais acceptées par `/v1/sync/push`.
2. **Synchronisables** : profil académique, calendrier, horaire, préférences, progression et événements pédagogiques légers. Elles utilisent un journal idempotent et versionné.
3. **Server-authoritative** : paiements, entitlement Premium et portefeuille IA. Le client ne peut jamais les pousser par le protocole générique Sync.

Un nouvel appareil reçoit un **snapshot canonique** puis seulement des deltas. Les mutations sont idempotentes par `mutation_id`; les objets modifiables utilisent une version de base et retournent un conflit explicite en cas de divergence. Les événements append-only sont immuables.

## Pourquoi
- protéger la confidentialité et les coûts de stockage ;
- empêcher un second appareil d'écraser silencieusement le premier ;
- permettre un offline-first réel ;
- séparer les données métier synchronisables des vérités financières ;
- permettre une future compaction du journal de changements grâce au snapshot.

## Conséquences
- les documents personnels ne sont pas restaurés automatiquement sur un autre appareil ;
- un utilisateur peut résoudre explicitement un conflit local/cloud ;
- la bibliothèque EduNova commune est versionnée et n'expose pas les clés de stockage objet ;
- les ressources Premium restent visibles dans le catalogue mais verrouillées jusqu'à entitlement valide.
