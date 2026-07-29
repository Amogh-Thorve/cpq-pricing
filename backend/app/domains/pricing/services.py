from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.pricing.repositories import PricingRuleRepository
from backend.app.domains.pricing.schemas import CalculatePriceRequest, CalculatePriceResponse, PricingRuleCreate, PricingRuleUpdate
from backend.app.domains.pricing.models import PricingRule
from backend.app.domains.catalog.services import CatalogService
from backend.app.core.exceptions import EntityNotFoundError

class PricingService:
    """
    Business service layer that acts as the Pricing Engine core.
    Responsible for resolving starting list prices and applying active pricing rules.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pricing_rule_repo = PricingRuleRepository(db)
        self.catalog_service = CatalogService(db)

    async def create_rule(self, schema: PricingRuleCreate) -> PricingRule:
        """
        Register a new pricing rule in the system.
        """
        return await self.pricing_rule_repo.create(schema)

    async def get_rule(self, rule_id: int) -> PricingRule:
        rule = await self.pricing_rule_repo.get_by_id(rule_id)
        if not rule:
            raise EntityNotFoundError(f"Pricing rule {rule_id} not found.")
        return rule

    async def calculate_line_item_price(self, request: CalculatePriceRequest) -> CalculatePriceResponse:
        """
        Main calculation engine that runs a pricing evaluation cycle for a item request.
        1. Resolves catalog list price.
        2. Fetches active pricing rules.
        3. Evaluates conditions (such as quantities or volume rules).
        4. Calculates discounts and final line price.
        """
        # Resolve initial base price using CatalogService
        base_price = await self.catalog_service.get_product_price(
            product_id=request.product_id,
            price_book_id=request.price_book_id
        )

        active_rules = await self.pricing_rule_repo.list_active()
        applied_rules: List[str] = []
        discount_percentage = request.requested_discount

        # Future placeholder execution logic:
        # Loop through rules, parse condition JSONs, modify discount_percentage, append applied_rules names.
        # e.g., if quantity >= rule.conditions.get("min_qty") ...
        for rule in active_rules:
            # Placeholder validation simulation
            min_qty = rule.conditions.get("min_qty")
            if min_qty is not None and request.quantity >= min_qty:
                if rule.actions.get("discount_type") == "percentage":
                    val = float(rule.actions.get("discount_value", 0))
                    discount_percentage += val
                    applied_rules.append(rule.name)

        # Apply manual or rule-derived discounts
        discount_multiplier = max(0.0, 1.0 - (discount_percentage / 100.0))
        discounted_price = float(base_price) * discount_multiplier
        total_amount = discounted_price * request.quantity

        return CalculatePriceResponse(
            product_id=request.product_id,
            base_price=float(base_price),
            discounted_price=discounted_price,
            total_amount=total_amount,
            applied_rules=applied_rules,
            margin_percentage=(1.0 - (0.6 * discounted_price) / (discounted_price or 1.0)) * 100.0  # Simulated 60% cost base margin check
        )
