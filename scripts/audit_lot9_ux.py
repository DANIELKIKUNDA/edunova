from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
checks = []

def require(path, *needles):
    text = (ROOT / path).read_text(encoding='utf-8')
    for needle in needles:
        ok = needle in text
        checks.append((f'{path}: {needle}', ok))
    return text

home = require('apps/mobile/lib/src/features/home/presentation/home_page.dart',
               'upcomingEventsProvider', 'todayPlanProvider', 'libraryCoursesProvider', '_greeting')
for demo in ['Biochimie', 'Physiologie générale', 'value: .48']:
    checks.append((f'home contains no demo literal {demo!r}', demo not in home))

require('apps/mobile/lib/src/shared/presentation/edunova_shell.dart', 'NavigationRail', 'NavigationBar', 'railBreakpoint')
require('apps/mobile/lib/src/features/engagement/presentation/engagement_page.dart',
        'Rythme', 'Rappels', 'Réglages', 'Historique récent', 'showTimePicker', 'systemNotificationsSupported')
require('apps/mobile/lib/src/features/audio/presentation/audio_summary_page.dart',
        'Slider(', 'SegmentedButton<double>', 'Mes repères audio', 'Texte du résumé', 'Aperçu audio gratuit')
require('apps/mobile/lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart',
        'getNotificationAppLaunchDetails', 'onDidReceiveNotificationResponse', "'link':n.deepLink")
require('apps/mobile/lib/src/core/theme/edunova_theme.dart', 'darkTheme' if False else 'navigationRailTheme', 'bottomSheetTheme', 'scrollbarTheme')
require('apps/mobile/lib/src/shared/presentation/widgets/premium_surface.dart', 'EduNovaPageBody', 'PremiumPanel', 'EmptyStateCard', 'SkeletonLine')

# lightweight structural sanity for changed sources
for rel in [
    'apps/mobile/lib/src/core/theme/tokens.dart',
    'apps/mobile/lib/src/core/theme/edunova_theme.dart',
    'apps/mobile/lib/src/shared/presentation/edunova_shell.dart',
    'apps/mobile/lib/src/shared/presentation/widgets/premium_surface.dart',
    'apps/mobile/lib/src/features/home/presentation/home_page.dart',
    'apps/mobile/lib/src/features/engagement/presentation/engagement_page.dart',
    'apps/mobile/lib/src/features/audio/presentation/audio_summary_page.dart',
    'apps/mobile/lib/src/features/engagement/application/local_notification_scheduler.dart',
    'apps/mobile/lib/src/features/engagement/infrastructure/local_notification_scheduler_native.dart',
    'apps/mobile/lib/src/app/edunova_app.dart',
]:
    text = (ROOT / rel).read_text(encoding='utf-8')
    checks.append((f'{rel}: braces balanced', text.count('{') == text.count('}')))
    checks.append((f'{rel}: parens balanced', text.count('(') == text.count(')')))

failed = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(('PASS ' if ok else 'FAIL ') + name)
if failed:
    print(f'\n{len(failed)} UX static check(s) failed.', file=sys.stderr)
    sys.exit(1)
print(f'\n{len(checks)} UX static checks PASS')
