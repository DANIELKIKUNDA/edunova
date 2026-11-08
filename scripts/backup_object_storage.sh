#!/usr/bin/env bash
set -euo pipefail
: "${CONTENT_STORAGE_BUCKET:?required}"
: "${BACKUP_DIR:?required}"
mkdir -p "$BACKUP_DIR"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"; out="$BACKUP_DIR/objects-$stamp"
mkdir -p "$out"
args=(); [[ -n "${CONTENT_STORAGE_ENDPOINT:-}" ]] && args+=(--endpoint-url "$CONTENT_STORAGE_ENDPOINT")
aws "${args[@]}" s3 sync "s3://$CONTENT_STORAGE_BUCKET" "$out/data" --only-show-errors
find "$out/data" -type f -print0 | sort -z | xargs -0 sha256sum > "$out/SHA256SUMS"
tar -C "$BACKUP_DIR" -czf "$out.tar.gz" "$(basename "$out")"
sha256sum "$out.tar.gz" > "$out.tar.gz.sha256"
rm -rf "$out"
echo "$out.tar.gz"
