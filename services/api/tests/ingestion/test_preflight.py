from __future__ import annotations

import io
import fitz
import pytest
from PIL import Image

from app.modules.ingestion.application.preflight import PreflightPolicy, PreflightValidator


def pdf_bytes(text='Physiologie générale'):
    doc=fitz.open(); page=doc.new_page(); page.insert_text((72,72),text); payload=doc.tobytes(); doc.close(); return payload


def png_bytes(size=(120,80)):
    b=io.BytesIO(); Image.new('RGB',size,'white').save(b,format='PNG'); return b.getvalue()


def test_preflight_detects_real_signature_not_extension():
    v=PreflightValidator()
    r=v.inspect(pdf_bytes(),filename='photo.jpg',declared_mime_type=None)
    assert r.detected_mime_type=='application/pdf' and r.page_count==1


def test_preflight_rejects_declared_mime_mismatch():
    with pytest.raises(ValueError,match='declared_mime_mismatch'):
        PreflightValidator().inspect(pdf_bytes(),filename='x.pdf',declared_mime_type='image/jpeg')


def test_preflight_rejects_unsupported_signature_and_size_limits():
    v=PreflightValidator(PreflightPolicy(max_file_bytes=10))
    with pytest.raises(ValueError,match='file_too_large'): v.inspect(b'x'*20,filename='x.bin')
    with pytest.raises(ValueError,match='unsupported_file_signature'): PreflightValidator().inspect(b'not a document',filename='x.pdf')


def test_preflight_image_dimensions():
    r=PreflightValidator().inspect(png_bytes(),filename='scan.png',declared_mime_type='image/png')
    assert r.page_count==1 and r.width_px==120 and r.height_px==80

def test_preflight_rejects_encrypted_pdf():
    doc=fitz.open(); doc.new_page(); payload=doc.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256,user_pw='secret',owner_pw='owner'); doc.close()
    with pytest.raises(ValueError,match='encrypted_pdf_not_supported'):
        PreflightValidator().inspect(payload,filename='secret.pdf',declared_mime_type='application/pdf')
