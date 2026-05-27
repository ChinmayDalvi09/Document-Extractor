"""
SQLAlchemy ORM models for the Document Extraction platform.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from app.database.db import Base


class ExtractionRecord(Base):
    """Stores every document extraction result in MySQL."""

    __tablename__ = "extraction_records"

    id             = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename       = Column(String(255), nullable=False)
    document_type  = Column(String(50),  nullable=False)
    structured_data = Column(JSON,        nullable=True)   # stores dict as JSON column
    created_at     = Column(DateTime,     default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"<ExtractionRecord id={self.id} filename={self.filename!r} "
            f"doc_type={self.document_type!r}>"
        )