#!/usr/bin/env python3
"""EduNova premium document processor CLI.

For platform/shared content and explicit opt-in processing only. Personal files
remain device-local by default in the student application.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'services' / 'api'))

from app.modules.document_engine.application.pipeline import PremiumDocumentPipeline
from app.modules.document_engine.infrastructure.artifacts import JsonArtifactWriter


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('document', type=Path)
    parser.add_argument('--out', type=Path, default=ROOT / 'tmp' / 'document-artifacts')
    parser.add_argument('--title')
    parser.add_argument('--no-ocr', action='store_true')
    parser.add_argument('--langs', default='fra+eng')
    args = parser.parse_args()

    pipeline = PremiumDocumentPipeline(enable_ocr=not args.no_ocr, ocr_languages=args.langs)
    result = pipeline.process(args.document, title=args.title)
    destination = args.out / result.document_id
    JsonArtifactWriter().write(result, destination)
    print(f'document_id={result.document_id}')
    print(f'sha256={result.fingerprint_sha256}')
    print(f'pages={len(result.pages)} sections={len(result.sections)} chunks={len(result.chunks)}')
    print(f'usable_text_ratio={result.quality.usable_text_ratio:.3f}')
    print(f'artifacts={destination}')
    if result.quality.warnings:
        print('warnings:')
        for warning in result.quality.warnings:
            print(f'- {warning}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
