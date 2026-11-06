#!/usr/bin/env bash
# Phase 14+15 Flutter certification gate, to run where Flutter SDK is installed.
# DO NOT mark frontend certified if any command fails.
set -euo pipefail
cd "$(dirname "$0")/../apps/mobile"
flutter --version
flutter pub get
flutter analyze --no-pub
# Fail quickly on tenant switches, privilege revocations and temporal privacy.
flutter test --no-pub test/campus_intelligence_tenant_transition_widget_test.dart test/campus_intelligence_archive_scope_widget_test.dart
# The project-wide Flutter suite remains mandatory for frontend closure.
flutter test --no-pub
# Device/build-specific certification remains scheduled for phases 19 and 23.
