from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ..domain.model import ProcessedDocument


class JsonArtifactWriter:
    def write(self, document: ProcessedDocument, destination: Path) -> None:
        destination.mkdir(parents=True, exist_ok=True)
        manifest = {
            "document_id": document.document_id,
            "fingerprint_sha256": document.fingerprint_sha256,
            "title": document.title,
            "kind": document.kind.value,
            "metadata": document.metadata,
            "quality": asdict(document.quality),
            "counts": {
                "pages": len(document.pages),
                "sections": len(document.sections),
                "chunks": len(document.chunks),
                "question_candidates": len(document.questions),
            },
        }
        _write_json(destination / "manifest.json", manifest)
        _write_json(destination / "sections.json", [asdict(item) for item in document.sections])
        _write_jsonl(destination / "pages.jsonl", [_enum_safe(asdict(item)) for item in document.pages])
        _write_jsonl(destination / "chunks.jsonl", [asdict(item) for item in document.chunks])
        _write_json(destination / "question_candidates.json", [asdict(item) for item in document.questions])


def _write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _enum_safe(value):
    if isinstance(value, dict):
        return {k: _enum_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_enum_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_enum_safe(v) for v in value]
    if hasattr(value, "value"):
        return value.value
    return value
