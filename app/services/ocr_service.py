"""
OCR Service – extracts text from uploaded image/PDF files using pytesseract.
Supports: JPEG, PNG, BMP, TIFF, GIF  +  PDF (via pdf2image, optional).
"""

import os
import shutil
import pytesseract
from pathlib import Path
from PIL import Image

from app.utils.logger import log_call, get_logger
from app.utils.exceptions import OCRError

logger = get_logger(__name__)

# ── Upload storage ────────────────────────────────────────────────────────────
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ── Tesseract path (Windows) ──────────────────────────────────────────────────
_TESSERACT_PATH = os.getenv(
    "TESSERACT_PATH",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
)

# Unconditionally set the path (on Windows it is rarely in PATH).
# If the file doesn't exist, pytesseract will raise a clear error later.
pytesseract.pytesseract.tesseract_cmd = _TESSERACT_PATH

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif"}
PDF_EXTENSION    = ".pdf"


@log_call
async def perform_ocr(file) -> tuple[str, str]:
    """
    Save the uploaded file and run OCR.
    Returns (extracted_text, saved_file_path).
    """
    file_path = UPLOAD_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise OCRError("Failed to save uploaded file", str(exc)) from exc

    suffix = file_path.suffix.lower()
    extracted_text = ""

    try:
        if suffix in IMAGE_EXTENSIONS:
            image = Image.open(file_path)
            extracted_text = pytesseract.image_to_string(image, lang="eng")

        elif suffix == PDF_EXTENSION:
            extracted_text = _ocr_pdf(file_path)

        else:
            raise OCRError(
                f"Unsupported file type: {suffix}",
                "Supported types: JPG, PNG, BMP, TIFF, GIF, PDF",
            )
    except OCRError:
        raise
    except Exception as exc:
        raise OCRError("OCR processing failed", str(exc)) from exc

    logger.info(
        "OCR complete for '%s' – extracted %d characters",
        file.filename,
        len(extracted_text),
    )
    return extracted_text.strip(), str(file_path)


def _ocr_pdf(file_path: Path) -> str:
    """Convert PDF pages to images then OCR each page."""
    try:
        from pdf2image import convert_from_path
        pages = convert_from_path(str(file_path), poppler_path=r"C:\Users\Chinmay Pratap Dalvi\Downloads\Release-26.02.0-0\poppler-26.02.0\Library\bin")
        print(len(pages))
    except ImportError:
        raise OCRError(
            "pdf2image not installed",
            "Install Poppler and run: pip install pdf2image",
        )

    try:
        pages = convert_from_path(str(file_path), dpi=300)
    except Exception as exc:
        raise OCRError("PDF conversion failed", str(exc)) from exc

    all_text = []
    for i, page in enumerate(pages, 1):
        page_text = pytesseract.image_to_string(page, lang="eng")
        all_text.append(page_text)
        logger.info("  OCR page %d/%d", i, len(pages))

    return "\n".join(all_text)