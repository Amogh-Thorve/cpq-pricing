from fastapi import APIRouter, Depends, status, Query
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.domains.auth.routes import get_current_user
from backend.app.domains.auth.models import User
from backend.app.domains.quotes.schemas import QuoteCreate, QuoteRead, QuoteUpdate
from backend.app.domains.quotes.services import QuoteService

router = APIRouter(prefix="/quotes", tags=["quotes-builder"])

@router.post("/", response_model=QuoteRead, status_code=status.HTTP_201_CREATED)
async def create_quote(
    schema: QuoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Onboard and validate a new sales quotation with calculated dynamic prices.
    """
    service = QuoteService(db)
    return await service.create_quote(creator_id=current_user.id, schema=schema)

@router.get("/", response_model=List[QuoteRead])
async def list_quotes(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all quotations.
    """
    service = QuoteService(db)
    return await service.list_quotes(limit=limit, offset=offset)

@router.get("/{quote_id}", response_model=QuoteRead)
async def get_quote(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed breakdown of a quote and all component lines.
    """
    service = QuoteService(db)
    return await service.get_quote(quote_id)

@router.post("/{quote_id}/revise", response_model=QuoteRead)
async def revise_quote(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Increment quote version, cloning products and resetting status to DRAFT.
    """
    service = QuoteService(db)
    return await service.revise_quote(quote_id)

@router.put("/{quote_id}", response_model=QuoteRead)
async def update_quote(
    quote_id: int,
    schema: QuoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Modify metadata status, or link to Salesforce.
    """
    service = QuoteService(db)
    quote = await service.get_quote(quote_id)
    return await service.quote_repo.update(quote, schema)
