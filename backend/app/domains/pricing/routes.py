from fastapi import APIRouter, Depends, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.domains.auth.routes import get_current_user
from backend.app.domains.auth.models import User
from backend.app.domains.pricing.schemas import CalculatePriceRequest, CalculatePriceResponse, PricingRuleCreate, PricingRuleRead
from backend.app.domains.pricing.services import PricingService

router = APIRouter(prefix="/pricing", tags=["pricing-engine"])

@router.post("/calculate", response_model=CalculatePriceResponse)
async def calculate_price(
    request: CalculatePriceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Evaluate pricing rules and manual overrides for a given product and quantity.
    """
    service = PricingService(db)
    return await service.calculate_line_item_price(request)

@router.post("/rules", response_model=PricingRuleRead, status_code=status.HTTP_201_CREATED)
async def create_pricing_rule(
    schema: PricingRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a new dynamic pricing rule. Restricted to admin/managers.
    """
    service = PricingService(db)
    return await service.create_rule(schema)

@router.get("/rules", response_model=List[PricingRuleRead])
async def list_active_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all active pricing configuration rules.
    """
    service = PricingService(db)
    return await service.pricing_rule_repo.list_active()
ClassSymbol = router
