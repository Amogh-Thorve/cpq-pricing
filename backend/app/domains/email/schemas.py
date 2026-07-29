from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class SendEmailRequest(BaseModel):
    quote_id: int
    recipient: EmailStr
    subject: str
    body: str

class EmailLogRead(BaseModel):
    id: int
    quote_id: int
    recipient: str
    subject: str
    sent_at: datetime
    status: str
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
