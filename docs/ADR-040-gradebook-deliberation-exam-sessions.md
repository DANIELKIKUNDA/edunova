# ADR-040 — LOT25 maximal: délibération, absences et sessions d'examen

## Décision
Le gradebook institutionnel distingue désormais présence, absence, absence justifiée et exemption. Une absence simple vaut zéro dans le calcul; une absence justifiée ou exemption maintient le résultat incomplet jusqu'à résolution académique. Les examens/tests/oraux/pratiques peuvent disposer de sessions planifiées. Le verrouillage de délibération bloque toute modification des notes; sa réouverture exceptionnelle est réservée à l'administration académique et exige un motif audité.

## Invariants
- aucune note numérique pour un statut non-présent;
- motif obligatoire pour absence justifiée/exemption;
- publication interdite tant que les résultats ne sont pas complets;
- verrouillage optimiste par row_version;
- réouverture exceptionnelle auditable et non accessible à un simple enseignant;
- session avec fin strictement postérieure au début.
