"""
LLM Service – extracts structured fields from OCR text.

Strategy (layered):
  1. Regex patterns per document type (fast, no API needed).
  2. OpenAI GPT-3.5-turbo fallback for fields that regex couldn't fill
     (only when OPENAI_API_KEY is set in .env).
"""

import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv

from app.utils.logger import log_call, get_logger
from app.utils.exceptions import LLMError

load_dotenv(Path(__file__).parent.parent.parent / ".env")
logger = get_logger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ── Regex patterns per doc type ───────────────────────────────────────────────
REGEX_PATTERNS: dict[str, dict[str, str]] = {
    "aadhaar": {
        "aadhaar_number": r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",
        "dob": r"(?:DOB|Date of Birth|Year of Birth)[:\s]*([0-9]{2}[\/\-][0-9]{2}[\/\-][0-9]{4}|[0-9]{4})",
        "gender":         r"\b(Male|Female|Transgender)\b",
        "name":           r"(?:Name[:\s]*)([A-Z][a-z]+(?: [A-Z][a-z]+)+)|(?s)^([A-Z][a-z]+(?: [A-Z][a-z]+){1,2})\s*\n.*?(?:DOB|Date of Birth|Male|Female)",
    },
    "driving_licence": {
        "license_number": r"\b[A-Z]{2}[- ]?\d{2}[- ]?\d{11}\b",
        "dob": r"(?:DOB|Date of Birth|Birth)[:\s]*([0-9]{2}[\/\-][0-9]{2}[\/\-][0-9]{4})",
        "vehicle_class":  r"(?:COV|Class of Vehicle|Vehicle Class|Authorization to Drive)[:\s]*([\w ,]+)",
        "name":           r"(?:Name[:\s]*)([A-Z][a-z]+(?: [A-Z][a-z]+)+)",
    },
    "passport": {
        "passport_number": r"\b[A-Z]{1,2}[0-9]{7}\b",
        "name":            r"(?:Surname[:\s]*)([A-Z]+)[\s\n]+(?:Given Name[s]?[:\s]*)([A-Z ]+)",
        "nationality":     r"(?:Nationality[:\s]*)([A-Z]+)",
        "expiry_date":     r"(?:Expiry|Expiry Date)[:\s]*(\d{2}[\/\-]\d{2}[\/\-]\d{4}|\d{2}\s\w{3}\s\d{4})",
    },
    "invoice": {
        "invoice_number": r"(?:Invoice(?: No| Number| #)?|Bill(?: No| Number| #)?)[.:\s\-]*([A-Z0-9\-\/]{3,})",
        "date":           r"(?:Date|Invoice Date)[:\s]*(\d{2}[\/\-]\d{2}[\/\-]\d{4})",
        "total_amount":   r"(?:Total|Grand Total|Amount Due|Total Amount)[:\s]*(?:Rs\.?|INR|₹)?\s*([\d,]+\.\d{2})",
        "vendor_name":    r"^([A-Z][A-Za-z\s&.,]+(?:Pvt\.?\s?Ltd\.?|LLP|Inc\.?|Co\.?|Enterprises|Solutions))",
    },
}


def _regex_extract(text: str, doc_type: str) -> dict:
    """Run regex patterns for the given doc_type against *text*."""
    patterns = REGEX_PATTERNS.get(doc_type, {})
    result = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            # Use the highest matching captured group if present, else full match
            if match.lastindex:
                matched_text = match.group(match.lastindex)
                result[field] = matched_text.strip() if matched_text else ""
            else:
                result[field] = match.group(0).strip()
        else:
            result[field] = ""
    return result


def _openai_extract(text: str, doc_type: str, template: dict) -> dict:
    """
    Use OpenAI to fill any blank fields from regex extraction.
    Only called when OPENAI_API_KEY is available.
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
    except ImportError as exc:
        raise LLMError("openai package not installed", str(exc)) from exc

    fields_list = ", ".join(template.keys()) if template else f"key fields from a {doc_type}"
    prompt = (
        f"Extract the following fields from this {doc_type} document OCR text.\n"
        f"Fields needed: {fields_list}\n\n"
        f"OCR Text:\n{text[:3000]}\n\n"
        "Return ONLY a valid JSON object with the field names as keys and extracted "
        "values as strings. Use empty string if a field is not found."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a document data extraction assistant."},
                {"role": "user",   "content": prompt},
            ],
            temperature=0,
            max_tokens=500,
        )
        content = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        content = re.sub(r"^```json\s*|```$", "", content, flags=re.MULTILINE).strip()
        return json.loads(content)
    except json.JSONDecodeError as exc:
        logger.warning("OpenAI returned non-JSON response: %s", exc)
        return {}
    except Exception as exc:
        raise LLMError("OpenAI API call failed", str(exc)) from exc


@log_call
def extract_fields(text: str, template: dict, doc_type: str = "unknown") -> dict:
    """
    Extract structured fields from OCR text.
    1) Regex extraction (always).
    2) OpenAI fill-in for blank fields (if API key is set).
    """
    # Step 1: regex
    extracted = _regex_extract(text, doc_type)

    # If no patterns exist (unknown doc type), seed from template keys
    if not extracted and template:
        extracted = {k: "" for k in template.keys()}

    # Step 2: LLM fill-in (only for blank fields + only if key present)
    blank_fields = [k for k, v in extracted.items() if not v]
    if blank_fields and OPENAI_API_KEY and OPENAI_API_KEY != "sk-your-key-here":
        logger.info("Calling OpenAI to fill %d blank field(s): %s", len(blank_fields), blank_fields)
        try:
            llm_result = _openai_extract(text, doc_type, template)
            for field in blank_fields:
                if field in llm_result and llm_result[field]:
                    extracted[field] = llm_result[field]
        except LLMError as exc:
            logger.warning("LLM extraction skipped (%s). Using regex-only result.", exc)
    else:
        if blank_fields:
            logger.info("Regex-only mode (no valid OPENAI_API_KEY). %d blank fields.", len(blank_fields))

    return extracted