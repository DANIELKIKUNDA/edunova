# ADR-0001 — Architecture hexagonale + offline-first

**Statut : accepté**

## Décision

EduNova adopte une architecture hexagonale pour le backend et une architecture feature-first inspirée Clean/Hexagonal dans Flutter. Les documents personnels sont local-first. Les opérations synchronisables passent par une outbox.

## Raisons

- protéger le métier des SDK externes ;
- permettre de changer de fournisseur IA, OCR ou Mobile Money ;
- fonctionner sur réseau intermittent ;
- faciliter les tests ;
- éviter une réécriture lorsque le pilote devient multi-université.

## Conséquences

Le code initial est plus structuré, mais le coût de maintenance et de changement fournisseur est fortement réduit.
