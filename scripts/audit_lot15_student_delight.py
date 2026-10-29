from pathlib import Path
root=Path(__file__).resolve().parents[1]
study=(root/'apps/mobile/lib/src/features/study_workspace/presentation/study_workspace_page.dart').read_text()
home=(root/'apps/mobile/lib/src/features/home/presentation/home_page.dart').read_text()
onboarding=(root/'apps/mobile/lib/src/features/onboarding/presentation/onboarding_page.dart').read_text()
checks={
 'mobile adaptive navigation':'NavigationBar' in study,
 'desktop three-zone workspace':'_desktop' in study and '_coach' in study and '_outline' in study,
 'focus mode':'Mode Focus' in study and 'Terminer le Focus' in study,
 'mastery journey':'Lecture' in study and 'Évaluation' in study and 'Maîtrise' in study,
 'flashcard delight':'À revoir' in study and 'Difficile' in study and 'Facile' in study and 'AnimatedSwitcher' in study,
 'quiz progressive CTA':'quizChoice<0 ? null' in study,
 'exam mode':'Exam Mode' in study,
 'micro-interaction':'TweenAnimationBuilder' in study,
 'offline affordance':'Disponible hors connexion' in study,
 'accessibility semantics':'Semantics' in study,
 'home greeting':'Prêt à avancer ?' in home,
 'home daily goal':'Objectif du jour atteint' in home,
 'home deadline hero':'PROCHAINE ÉCHÉANCE' in home,
 'onboarding academic personalization':'Configure ton parcours' in onboarding,
 'optional university':'facultative' in onboarding,
 'version mobile':'version: 0.16.2+27' in (root/'apps/mobile/pubspec.yaml').read_text(),
 'version admin':'version: 0.16.2+27' in (root/'apps/admin/pubspec.yaml').read_text(),
 'api version':'version="0.16.2"' in (root/'services/api/app/main.py').read_text(),
 'student delight documentation':(root/'docs/LOT15_STUDENT_DELIGHT_v0.16.2.md').exists(),
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print(f'\n{sum(checks.values())}/{len(checks)} PASS')
raise SystemExit(1 if failed else 0)
