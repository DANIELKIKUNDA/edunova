# ADR-0006 — Quota IA cyclique et crédits achetés séparés

Le portefeuille IA possède deux compartiments :

1. **quota inclus** : renouvelé à la valeur du cycle Premium ; il ne s'accumule pas indéfiniment ;
2. **crédits achetés** : persistants jusqu'à consommation.

La consommation utilise d'abord le quota inclus puis les crédits achetés. Le backend reste autoritaire et refuse tout solde négatif.
