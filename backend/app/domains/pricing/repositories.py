from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.pricing.models import PricingRule
from backend.app.domains.pricing.schemas import PricingRuleCreate, PricingRuleUpdate

class PricingRuleRepository:
    """
    Handles persistence logic for Dynamic Pricing Rules.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, rule_id: int) -> Optional[PricingRule]:
        result = await self.db.execute(select(PricingRule).where(PricingRule.id == rule_id))
        return result.scalars().first()

    async def list_active(self) -> List[PricingRule]:
        """
        List all rules currently flagged as active.
        """
        result = await self.db.execute(
            select(PricingRule).where(PricingRule.is_active == True)
        )
        return list(result.scalars().all())

    async def create(self, schema: PricingRuleCreate) -> PricingRule:
        db_rule = PricingRule(**schema.model_dump())
        self.db.add(db_rule)
        await self.db.flush()
        return db_rule

    async def update(self, db_rule: PricingRule, schema: PricingRuleUpdate) -> PricingRule:
        for field, value in schema.model_dump(exclude_unset=True).items():
            setattr(db_rule, field, value)
        self.db.add(db_rule)
        await self.db.flush()
        return db_rule
