from fastapi import APIRouter, Depends, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.domains.auth.routes import get_current_user
from backend.app.domains.auth.models import User
from backend.app.domains.email.schemas import SendEmailRequest, EmailLogRead
from backend.app.domains.email.services import EmailService

router = APIRouter(prefix="/emails", tags=["email-dispatcher"])

@router.post("/send", response_model=EmailLogRead, status_code=status.HTTP_201_CREATED)
async def send_quote_proposal(
    request: SendEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send proposal email with latest generated PDF quote attachment.
    """
    service = EmailService(db)
    return await service.send_quote_email(request)

@router.get("/quote/{quote_id}", response_model=List[EmailLogRead])
async def list_quote_emails(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all outbound email audit logs sent for a specific quote ID.
    """
    service = EmailService(db)
    return await service.email_repo.list_for_quote(quote_id)
