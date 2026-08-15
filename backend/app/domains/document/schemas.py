from pydantic import BaseModel
from datetime import datetime

class GenerateDocumentRequest(BaseModel):
    quote_id: int
    template_name: str = "default_proposal"

class DocumentRead(BaseModel):
    id: int
    quote_id: int
    file_path: str
    generated_at: datetime
    created_by_id: int

    class Config:
        from_attributes = True
