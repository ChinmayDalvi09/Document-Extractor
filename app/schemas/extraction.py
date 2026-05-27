"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class ExtractionResponse(BaseModel):
    """Returned by POST /extract."""
    model_config = ConfigDict(from_attributes=True)

    id:               int
    filename:         str
    document_type:    str
    structured_data:  Dict[str, Any]
    created_at:       datetime


class RecordOut(BaseModel):
    """Returned by GET /records and GET /records/{id}."""
    model_config = ConfigDict(from_attributes=True)

    id:              int
    filename:        str
    document_type:   str
    structured_data: Optional[Dict[str, Any]]
    created_at:      datetime


class RecordListResponse(BaseModel):
    total:   int
    records: List[RecordOut]
