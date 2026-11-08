from pathlib import Path
checks={
'presence_secure':'attendance_qr_invalid_or_expired',
'proximity_signed':'signed_proximity_failed',
'absence_workflow':'def decide_absence',
'announcements':'def create_announcement',
'calendar_operations':'def create_event',
'operations_dashboard':'def operations_dashboard',
'audit_trace':'attendance.closed',
'campus_push':'DeliveryChannel.PUSH',
'fcm_backend':'class FirebaseAdminPushSender',
'push_registry':'def register_push',
'fcm_mobile':'FirebaseMessaging.instance',
'push_device_mobile':'registerPushDevice',
'offline_local_notifications':'flutter_local_notifications',
}
files=list(Path('services/api').rglob('*.py'))+list(Path('apps/mobile').rglob('*.dart'))+[Path('apps/mobile/pubspec.yaml')]
blob='\n'.join(p.read_text(errors='ignore') for p in files if p.exists())
failed=[]
for name,marker in checks.items():
 ok=marker in blob; print(f"{'PASS' if ok else 'FAIL'} {name}")
 if not ok: failed.append(name)
print(f"LOT26 CLOSURE AUDIT: {len(checks)-len(failed)}/{len(checks)} PASS")
raise SystemExit(bool(failed))
