from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.domains.auth.routes import get_current_user
from backend.app.domains.auth.models import User
from backend.app.domains.ai.schemas import (
    CustomerSummaryRequest, CustomerSummaryResponse,
    QuoteSummaryRequest, QuoteSummaryResponse,
    EmailDraftRequest, EmailDraftResponse,
    ProductRecommendationRequest, ProductRecommendationResponse
)
from backend.app.domains.ai.services import AIService

router = APIRouter(prefix="/ai", tags=["ai-copilot"])

@router.post("/customer-summary", response_model=CustomerSummaryResponse)
async def get_customer_summary(
    request: CustomerSummaryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate an AI-powered executive summary of a customer profile.
    """
    service = AIService(db)
    return await service.summarize_customer(request)

@router.post("/quote-summary", response_model=QuoteSummaryResponse)
async def get_quote_summary(
    request: QuoteSummaryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate an AI analysis of a quote, explaining pricing variations and margin indicators.
    """
    service = AIService(db)
    return await service.summarize_quote(request)

@router.post("/draft-email", response_model=EmailDraftResponse)
async def draft_proposal_email(
    request: EmailDraftRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Draft an outbound email body text contextually tailored to the target quote and customer.
    """
    service = AIService(db)
    return await service.draft_email(request)

@router.post("/recommendations", response_model=ProductRecommendationResponse)
async def get_recommendations(
    request: ProductRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Provide intelligence-driven up-sell and cross-sell recommendations.
    """
    service = AIService(db)
    return await service.recommend_products(request)
