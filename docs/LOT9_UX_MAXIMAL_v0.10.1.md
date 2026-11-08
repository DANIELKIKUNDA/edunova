# LOT 9 — UX/UI maximal v0.10.1

## Objectif
Faire du LOT 9 une expérience premium visible et pas seulement un moteur d'engagement solide.

## Changements majeurs
- Design system enrichi : tokens de couleur, espace, rayons, motion et largeurs adaptatives.
- Navigation adaptative : barre inférieure mobile, NavigationRail tablette/desktop.
- Accueil branché sur les vraies données : échéances, plan du jour, objectif d'activité et cours suivis. Suppression des exemples statiques historiques.
- Centre `Mon rythme` en trois espaces : Rythme, Rappels, Réglages.
- Visualisation 7 jours, objectif quotidien, meilleure série, quiz et minutes réelles.
- Préférences complètes : heures calmes modifiables, heure d'étude préférée, plafond quotidien, objectif, catégories de notifications.
- Permission de notification précédée d'une explication claire et volontaire.
- Historique récent des rappels.
- Deep-link notification : toucher une notification ouvre désormais son écran cible, y compris après lancement depuis application fermée sur Android/iOS.
- Capacité plateforme explicite : l'UI ne promet pas de notification locale native sur une plateforme non supportée.
- Lecteur audio premium : hero, slider, temps restant estimé, reprise, changement de vitesse en lecture, repères en %, transcript repliable et états gratuit/Premium propres.
- États Loading / Empty / Error réutilisables.
- Respect de `MediaQuery.disableAnimations` pour réduire les animations lorsque demandé.
- Premiers tests widget avec facteur de texte ×2.

## Principes UX verrouillés
1. Aucune donnée de démonstration sur les écrans de production.
2. Une notification doit mener à une action utile.
3. Une permission système n'est jamais demandée sans explication préalable.
4. Les streaks restent informatifs, jamais culpabilisants.
5. L'audio complet reste Premium ; l'aperçu gratuit montre la valeur sans bloquer la découverte.
6. Navigation et largeur s'adaptent à Android/iPhone/PWA/Windows.
7. Tous les états vides doivent expliquer l'action suivante.
8. Les icônes seules disposent d'un tooltip ou d'une sémantique explicite.

## Limites honnêtes
- L'audio média sur écran verrouillé et commandes lock-screen doit encore être certifié sur appareils réels.
- Les notifications Web/PWA dépendent du canal push distant ; le scheduler local natif est Android/iOS.
- Les captures visuelles/golden tests réels exigent Flutter SDK et les plateformes de rendu.
