#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/services/api"
python -m compileall -q app tests
pytest -q
cd "$ROOT/apps/mobile"
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
