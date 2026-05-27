"""
Custom exception hierarchy for the Document Extraction platform.
Follows SOLID / OOP principles — each concern has its own exception type.
"""


class DocumentExtractorError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, detail: str = ""):
        super().__init__(message)
        self.detail = detail


class OCRError(DocumentExtractorError):
    """Raised when OCR processing fails (file unreadable, Tesseract not found, etc.)."""


class ClassificationError(DocumentExtractorError):
    """Raised when the document type cannot be determined."""


class TemplateNotFoundError(DocumentExtractorError):
    """Raised when a template JSON file for a doc type is missing."""


class LLMError(DocumentExtractorError):
    """Raised when the LLM call fails (network, quota, invalid response, etc.)."""


class DatabaseError(DocumentExtractorError):
    """Raised on any database persistence failure."""
