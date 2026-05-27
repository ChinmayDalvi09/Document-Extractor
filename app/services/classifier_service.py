"""
Classifier Service – determines document type from extracted OCR text.
Uses keyword scoring + structural pattern fallback for robustness
across partial/noisy OCR output and generic filenames.
"""

import re
from app.utils.logger import log_call
from app.utils.exceptions import ClassificationError

# ── Keyword maps (lower-case) ────────────────────────────────────────────────
KEYWORD_MAP = {
    "aadhaar": [
        # explicit labels
        "aadhaar", "aadhar", "adhaar", "adhar", "uid",
        "unique identification", "unique identity", "uidai",
        "government of india", "enrollment no", "enrolment no",
        # Hindi transliterations common in OCR
        "आधार", "भारत सरकार",
        # fields that appear on Aadhaar
        "your aadhaar", "male", "female", "dob", "date of birth",
        "year of birth", "s/o", "d/o", "w/o", "address",
    ],
    "driving_licence": [
        "driving licence", "driving license", "driver license",
        "dl no", "dl number", "dl:", "licence no", "license no",
        "transport department", "rto", "vehicle class", "motor vehicle",
        "state transport", "cov", "class of vehicle",
        "validity", "non-transport", "transport",
        "badge no", "blood group", "issuing authority",
    ],
    "passport": [
        "passport", "republic of india", "nationality",
        "place of birth", "place of issue", "date of issue", "date of expiry",
        "surname", "given name", "given names",
        "ministry of external affairs", "type", "country code",
        "personal no", "personal number",
        # MRZ line markers
        "<<",
    ],
    "invoice": [
        "invoice", "tax invoice", "proforma invoice",
        "bill", "bill of supply", "delivery challan",
        "gstin", "gst no", "gst number", "gst registration",
        "total amount", "amount due", "grand total", "subtotal",
        "vendor", "supplier", "buyer", "purchaser",
        "purchase order", "po no", "hsn", "sac",
        "quantity", "rate", "taxable value", "igst", "cgst", "sgst",
        "payment terms", "due date", "bank details",
    ],
}

# ── Structural patterns (regex over raw OCR text) ────────────────────────────
# These fire when keyword scoring is still zero/tied
STRUCTURAL_PATTERNS = [
    # 12-digit Aadhaar number (with optional spaces/dashes)
    ("aadhaar",         r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
    # Indian DL format: XX00 00000000000
    ("driving_licence", r"\b[A-Z]{2}\d{2}[\s\-]?\d{2}[\s\-]?\d{7}\b"),
    # Passport number: 1 letter + 7 digits
    ("passport",        r"\b[A-Z]\d{7}\b"),
    # MRZ lines (two long uppercase lines with <<)
    ("passport",        r"[A-Z0-9<]{40,}"),
    # GSTIN: 15-character GST number
    ("invoice",         r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{3}\b"),
]


@log_call
def classify_document(text: str, filename: str = "") -> str:
    """
    Classify a document by scoring OCR text + filename against keyword maps,
    then fall back to structural regex patterns.
    Returns the best-matching doc type, or 'unknown'.
    """
    combined = (text + " " + filename).lower()
    scores: dict[str, int] = {doc_type: 0 for doc_type in KEYWORD_MAP}

    # 1. Keyword scoring
    for doc_type, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if kw in combined:
                scores[doc_type] += 1

    best_type, best_score = max(scores.items(), key=lambda x: x[1])

    if best_score > 0:
        return best_type

    # 2. Structural pattern fallback (raw OCR text, case-sensitive)
    struct_scores: dict[str, int] = {doc_type: 0 for doc_type in KEYWORD_MAP}
    for doc_type, pattern in STRUCTURAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            struct_scores[doc_type] += 1

    best_struct_type, best_struct_score = max(struct_scores.items(), key=lambda x: x[1])
    if best_struct_score > 0:
        return best_struct_type

    return "unknown"