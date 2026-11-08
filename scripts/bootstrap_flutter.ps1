$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Mobile = Join-Path $Root "apps/mobile"

if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
  throw "Flutter n'est pas installé ou n'est pas dans PATH."
}

Push-Location $Mobile
try {
  flutter create --platforms=android,ios,web,windows .
  flutter pub get
  dart run build_runner build --delete-conflicting-outputs
  flutter analyze
  flutter test
}
finally {
  Pop-Location
}
