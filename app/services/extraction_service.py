"""
Extraction Service – orchestrates the full document extraction pipeline
and persists results to MySQL.
"""

from sqlalchemy.orm import Session

from app.services.ocr_service import perform_ocr
from app.services.classifier_service import classify_document
from app.services.template_service import load_template
from app.services.llm_service import extract_fields
from app.database.models import ExtractionRecord
from app.utils.logger import log_call, get_logger
from app.utils.exceptions import DatabaseError

logger = get_logger(__name__)


@log_call
async def process_document(file, db: Session) -> ExtractionRecord:
    """
    Full pipeline:
      1. OCR  →  raw text
      2. Classify  →  document type
      3. Load template  →  expected fields
      4. LLM/regex extract  →  structured data
      5. Persist  →  MySQL
    Returns the saved ExtractionRecord ORM object.
    """
    # 1. OCR
    text, file_path = await perform_ocr(file)

    # 2. Classify
    doc_type = classify_document(text, file.filename)
    logger.info("Classified '%s' as '%s'", file.filename, doc_type)

    # 3. Template
    template = load_template(doc_type)

    # 4. Extract fields
    structured_data = extract_fields(text, template, doc_type)

    # 5. Persist to MySQL
    record = ExtractionRecord(
        filename=file.filename,
        document_type=doc_type,
        structured_data=structured_data,
    )
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info("Saved ExtractionRecord id=%s for '%s'", record.id, file.filename)
    except Exception as exc:
        db.rollback()
        raise DatabaseError("Failed to save extraction record", str(exc)) from exc

    return record