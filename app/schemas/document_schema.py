from pydantic import BaseModel
from typing import Dict

class DocumentResponse(BaseModel):
    filename: str
    document_type: str
    extracted_text: str
    structured_data: Dict