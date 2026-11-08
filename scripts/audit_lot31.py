from pathlib import Path
R=Path(__file__).resolve().parents[1]
checks={'pilot service':'pilot_readiness' in (R/'services/api/app/modules/pilot_readiness/application/service.py').as_posix(),'pilot tests':(R/'services/api/tests/test_pilot_readiness_lot31.py').exists(),'pwa manifest':(R/'apps/mobile/web/manifest.json').exists(),'offline fallback':(R/'apps/mobile/web/offline.html').exists(),'service worker':(R/'apps/mobile/web/sw.js').exists(),'pilot ui':(R/'apps/mobile/lib/src/features/pilot/presentation/pilot_center_page.dart').exists(),'branding':'From Volcano Tech' in (R/'apps/mobile/lib/src/features/pilot/presentation/pilot_center_page.dart').read_text()}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print(f"LOT31 AUDIT: {sum(checks.values())}/{len(checks)} PASS")
raise SystemExit(0 if all(checks.values()) else 1)
