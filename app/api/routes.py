"""
API Routes – FastAPI router for the Document Extraction platform.
Endpoints:
  GET  /           → health check
  POST /extract    → upload & process document
  GET  /records    → list all extraction records
  GET  /records/{id} → get single record
  DELETE /records/{id} → delete record
"""

from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import ExtractionRecord
from app.schemas.extraction import ExtractionResponse, RecordOut, RecordListResponse
from app.services.extraction_service import process_document
from app.utils.exceptions import (
    DocumentExtractorError,
    OCRError,
    DatabaseError,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/bmp",
    "image/tiff", "image/gif", "application/pdf",
}


# ── Health ────────────────────────────────────────────────────────────────────
@router.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "Document Extractor API is running 🚀"}


# ── Extract ───────────────────────────────────────────────────────────────────
@router.post(
    "/extract",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Extraction"],
    summary="Upload a document and extract structured fields",
)
async def extract_document(
    file: UploadFile = File(..., description="Image (JPG/PNG/BMP/TIFF) or PDF"),
    db: Session = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. "
                   f"Allowed: JPEG, PNG, BMP, TIFF, GIF, PDF.",
        )
    try:
        record = await process_document(file, db)
        return ExtractionResponse(
            id=record.id,
            filename=record.filename,
            document_type=record.document_type,
            structured_data=record.structured_data or {},
            created_at=record.created_at,
        )
    except OCRError as exc:
        logger.error("OCR failed: %s", exc)
        raise HTTPException(status_code=422, detail=f"OCR Error: {exc}")
    except DatabaseError as exc:
        logger.error("DB failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Database Error: {exc}")
    except DocumentExtractorError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── Records ───────────────────────────────────────────────────────────────────
@router.get(
    "/records",
    response_model=RecordListResponse,
    tags=["Records"],
    summary="List all past extraction records",
)
def list_records(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    records = (
        db.query(ExtractionRecord)
        .order_by(ExtractionRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    total = db.query(ExtractionRecord).count()
    return RecordListResponse(total=total, records=records)


@router.get(
    "/records/{record_id}",
    response_model=ExtractionResponse,
    tags=["Records"],
    summary="Get a single extraction record by ID",
)
def get_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(ExtractionRecord).filter(ExtractionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found")
    return ExtractionResponse(
        id=record.id,
        filename=record.filename,
        document_type=record.document_type,
        structured_data=record.structured_data or {},
        created_at=record.created_at,
    )


@router.delete(
    "/records/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Records"],
    summary="Delete a single extraction record",
)
def delete_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(ExtractionRecord).filter(ExtractionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found")
    db.delete(record)
    db.commit()
    logger.info("Deleted record id=%s", record_id)