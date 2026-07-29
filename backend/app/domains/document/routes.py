from fastapi import APIRouter, Depends, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.domains.auth.routes import get_current_user
from backend.app.domains.auth.models import User
from backend.app.domains.document.schemas import GenerateDocumentRequest, DocumentRead
from backend.app.domains.document.services import DocumentService

router = APIRouter(prefix="/documents", tags=["documents-generation"])

@router.post("/generate", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def generate_document(
    request: GenerateDocumentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a formal PDF proposal for an approved sales quotation.
    """
    service = DocumentService(db)
    return await service.generate_pdf(creator_id=current_user.id, request=request)

@router.get("/quote/{quote_id}", response_model=List[DocumentRead])
async def list_quote_documents(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all historical generated PDF proposals for a specific quote ID.
    """
    service = DocumentService(db)
    return await service.doc_repo.list_for_quote(quote_id)
