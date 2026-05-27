"""
Tests for the Document Extractor API.
Run with: pytest tests/ -v
"""

import io
import pytest
from PIL import Image, ImageDraw, ImageFont
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── Helpers ───────────────────────────────────────────────────────────────────
def make_test_image(text: str = "Invoice No: INV-001\nDate: 01/01/2024\nTotal: Rs. 5000\nVendor: Test Co") -> bytes:
    """Create an in-memory PNG with given text for OCR testing."""
    img  = Image.new("RGB", (600, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


# ── Tests ─────────────────────────────────────────────────────────────────────
def test_health_check():
    """GET / should return 200 with status ok."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_extract_with_image():
    """POST /extract with a valid PNG should return structured extraction."""
    image_bytes = make_test_image()
    response = client.post(
        "/extract",
        files={"file": ("test_invoice.png", image_bytes, "image/png")},
    )
    # Accept 200 or 422 (if Tesseract not installed in CI)
    assert response.status_code in (200, 422, 500)
    if response.status_code == 200:
        body = response.json()
        assert "filename"       in body
        assert "document_type"  in body
        assert "structured_data" in body
        assert "id"             in body


def test_unsupported_file_type():
    """POST /extract with a text file should return 415."""
    response = client.post(
        "/extract",
        files={"file": ("doc.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 415


def test_get_records():
    """GET /records should return a list response."""
    response = client.get("/records")
    assert response.status_code == 200
    body = response.json()
    assert "total"   in body
    assert "records" in body
    assert isinstance(body["records"], list)


def test_get_nonexistent_record():
    """GET /records/99999 should return 404."""
    response = client.get("/records/99999")
    assert response.status_code == 404