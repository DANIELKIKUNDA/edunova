#!/usr/bin/env bash
set -euo pipefail
: "${CONTENT_STORAGE_BUCKET:?required}"; : "${RESTORE_ARCHIVE:?required}"
[[ "${CONFIRM_OBJECT_RESTORE:-}" == "RESTORE" ]] || { echo 'Set CONFIRM_OBJECT_RESTORE=RESTORE' >&2; exit 2; }
sha256sum -c "$RESTORE_ARCHIVE.sha256"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
tar -xzf "$RESTORE_ARCHIVE" -C "$tmp"; root="$(find "$tmp" -mindepth 1 -maxdepth 1 -type d | head -1)"
(cd "$root" && sha256sum -c SHA256SUMS)
args=(); [[ -n "${CONTENT_STORAGE_ENDPOINT:-}" ]] && args+=(--endpoint-url "$CONTENT_STORAGE_ENDPOINT")
aws "${args[@]}" s3 sync "$root/data" "s3://$CONTENT_STORAGE_BUCKET" --only-show-errors
