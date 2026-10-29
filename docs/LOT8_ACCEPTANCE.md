# LOT 8 — Critères d'acceptation

## Backend — certifiés ici
- [x] Baseline v0.8.1 repasse 181/181 avant modification.
- [x] Grant opaque sans fuite de `storage_locator`.
- [x] Token lié au compte et à la ressource.
- [x] Premium revalidé au moment de la livraison.
- [x] `purpose=offline` contrôlé.
- [x] Range explicite, ouvert et suffixe.
- [x] Multi-range rejeté.
- [x] 416 avec `Content-Range: bytes */TOTAL`.
- [x] Taille stockage/catalogue vérifiée.
- [x] SHA-256 stockage/catalogue vérifié lorsque disponible.
- [x] Path traversal storage local rejeté.
- [x] Proxy `206` reprend exactement les octets demandés.
- [x] Rate limiting grant.
- [x] Suite backend complète verte.

## Flutter — à certifier sur machine
- [ ] `flutter pub get` avec crypto/connectivity_plus.
- [ ] Drift v13 -> v14.
- [ ] `build_runner` sans conflit.
- [ ] `flutter analyze` 0 erreur.
- [ ] `flutter test` complet.
- [ ] Android : interruption réseau à 30 %, reprise sans recommencer.
- [ ] Android : ETag modifié -> redémarrage propre.
- [ ] Android : checksum faux -> fichier non finalisé.
- [ ] Windows : même scénarios Range/reprise/checksum.
- [ ] PWA : chunks persistants après refresh navigateur.
- [ ] PWA : reprise après fermeture/réouverture.
- [ ] Cache cleanup ne supprime jamais un document personnel.
- [ ] Contenu épinglé jamais supprimé par cleanup.
- [ ] Cours suivi protégé si politique active.
- [ ] Entitlement Premium expiré : ressource premium conservée physiquement mais non ouverte.
