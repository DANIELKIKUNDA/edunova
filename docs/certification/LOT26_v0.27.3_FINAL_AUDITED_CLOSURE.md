# LOT 26 — v0.27.3 FINAL Audited Closure

This checkpoint corrects the notification closure after a contradictory audit of v0.27.2.

## Verified scope
- Secure attendance: rotating signed QR, anti-replay, device binding, geofence/risk review, independent signed proximity proof.
- Real teaching-session linkage and automatic absence materialization at attendance closure.
- Absence justification workflow with human approval/rejection and audit trail.
- Institutional announcements with audience targeting, scheduling/retraction and notification intents.
- Academic operations calendar with audited state transitions.
- Operations dashboard and traceability.
- Offline/local notifications remain available on-device.
- Remote institutional notifications are server-originated PUSH intents.
- Backend FCM adapter uses Firebase Admin SDK and registered device tokens.
- Flutter mobile initializes Firebase Messaging on Android/iOS, requests permission, registers/refreshed FCM tokens through `/v1/engagement/push-devices`.
- Push is best-effort and never blocks offline-first startup.

## Executed evidence
- Targeted LOT26 + engagement + migration tests: 31 PASS.
- Full backend regression: 426 PASS.
- Python compileall: PASS.
- Closure source audit: 13/13 PASS.

## OPEN-machine / deployment evidence
The repository intentionally does not contain Firebase project credentials or platform configuration secrets. Real-device delivery requires the deployment-owned Firebase configuration (`google-services.json` / Apple configuration as applicable), Google service credentials, `FCM_ENABLED=true`, Flutter dependency resolution/build, and Android/iOS device delivery tests. BLE/NFC/managed-Wi-Fi proximity and hardware attestation likewise remain physical/infrastructure certification items.
