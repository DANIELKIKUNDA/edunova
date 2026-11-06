#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/apps/mobile"
command -v flutter >/dev/null || { echo "Flutter absent du PATH"; exit 1; }
flutter create --platforms=android,ios,web,windows .
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
