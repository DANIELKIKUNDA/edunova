from __future__ import annotations

from pathlib import Path

import fitz

from app.modules.document_engine.application.chunking import build_chunks
from app.modules.document_engine.application.pipeline import PremiumDocumentPipeline
from app.modules.document_engine.application.search import search_chunks
from app.modules.document_engine.infrastructure.text import normalize_text


def _sample_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((60, 80), "CHAPITRE 1 — CELLULE", fontsize=19)
    page.insert_text((60, 120), "La membrane plasmique sépare le milieu intracellulaire du milieu extracellulaire.", fontsize=11)
    page.insert_text((60, 150), "1.1 Composition", fontsize=15)
    page.insert_text((60, 180), "Elle contient notamment des phospholipides et des protéines membranaires.", fontsize=11)
    page2 = doc.new_page()
    page2.insert_text((60, 80), "CHAPITRE 2 — TRANSPORT", fontsize=19)
    page2.insert_text((60, 120), "La diffusion simple suit le gradient de concentration sans dépense directe d'ATP.", fontsize=11)
    doc.save(path)
    doc.close()


def test_normalize_text_dehyphenates() -> None:
    assert normalize_text("mem-\nbrane   plasmique") == "membrane plasmique"


def test_pipeline_is_deterministic_and_structured(tmp_path: Path) -> None:
    pdf = tmp_path / "physiologie.pdf"
    _sample_pdf(pdf)
    engine = PremiumDocumentPipeline(enable_ocr=False)
    first = engine.process(pdf, title="Physiologie")
    second = engine.process(pdf, title="Physiologie")
    assert first.document_id == second.document_id
    assert first.fingerprint_sha256 == second.fingerprint_sha256
    assert len(first.pages) == 2
    assert len(first.sections) >= 2
    assert len(first.chunks) >= 2
    assert first.quality.usable_text_ratio == 1.0


def test_search_returns_relevant_page(tmp_path: Path) -> None:
    pdf = tmp_path / "physiologie.pdf"
    _sample_pdf(pdf)
    document = PremiumDocumentPipeline(enable_ocr=False).process(pdf)
    hits = search_chunks(document.chunks, "diffusion gradient ATP")
    assert hits
    assert hits[0].start_page == 2
    assert "gradient" in hits[0].excerpt.lower()


def test_chunks_have_token_budget(tmp_path: Path) -> None:
    pdf = tmp_path / "physiologie.pdf"
    _sample_pdf(pdf)
    document = PremiumDocumentPipeline(enable_ocr=False).process(pdf)
    assert all(chunk.token_estimate > 0 for chunk in document.chunks)


def test_ocr_photo_pipeline(tmp_path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new('RGB', (1800, 700), 'white')
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 58)
    except OSError:
        font = ImageFont.load_default()
    draw.text((80, 120), 'INTERROGATION DE CHIMIE', fill='black', font=font)
    draw.text((80, 250), '1. Calculer la quantite de matiere.', fill='black', font=font)
    draw.text((80, 360), '2. Donner la formule de concentration molaire.', fill='black', font=font)
    path = tmp_path / 'interro.jpg'
    image.save(path, quality=95)

    document = PremiumDocumentPipeline(enable_ocr=True, ocr_languages='fra+eng').process(path)
    assert document.quality.pages_ocr == 1
    assert 'CHIMIE' in document.pages[0].text.upper()
    assert document.pages[0].confidence is None or document.pages[0].confidence > 0.40


def test_question_candidates_from_interrogation_photo(tmp_path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new('RGB', (1800, 760), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 52)
    draw.text((80, 90), 'INTERROGATION DE PHYSIQUE', fill='black', font=font)
    draw.text((80, 240), '1. Definir la vitesse moyenne.', fill='black', font=font)
    draw.text((80, 355), '2. Calculer la distance parcourue.', fill='black', font=font)
    path = tmp_path / 'questions.jpg'
    image.save(path, quality=95)

    document = PremiumDocumentPipeline(enable_ocr=True, ocr_languages='fra+eng').process(path)
    assert len(document.questions) >= 2
    assert document.questions[0].start_page == 1
    assert document.questions[0].confidence >= 0.8
