from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.configuration.models import ConfigurationRule
from backend.app.domains.configuration.schemas import ConfigurationRuleCreate, ConfigurationRuleUpdate

class ConfigurationRuleRepository:
    """
    Handles persistence logic for Configuration Rules (exclusion, dependencies, recommendations).
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, rule_id: int) -> Optional[ConfigurationRule]:
        result = await self.db.execute(select(ConfigurationRule).where(ConfigurationRule.id == rule_id))
        return result.scalars().first()

    async def list_active(self) -> List[ConfigurationRule]:
        result = await self.db.execute(
            select(ConfigurationRule).where(ConfigurationRule.is_active == True)
        )
        return list(result.scalars().all())

    async def get_rules_for_products(self, product_ids: List[int]) -> List[ConfigurationRule]:
        """
        Retrieve active configuration rules triggered by a set of product IDs.
        """
        result = await self.db.execute(
            select(ConfigurationRule)
            .where(
                ConfigurationRule.is_active == True,
                ConfigurationRule.product_id.in_(product_ids)
            )
        )
        return list(result.scalars().all())

    async def create(self, schema: ConfigurationRuleCreate) -> ConfigurationRule:
        db_rule = ConfigurationRule(**schema.model_dump())
        self.db.add(db_rule)
        await self.db.flush()
        return db_rule

    async def update(self, db_rule: ConfigurationRule, schema: ConfigurationRuleUpdate) -> ConfigurationRule:
        for field, value in schema.model_dump(exclude_unset=True).items():
            setattr(db_rule, field, value)
        self.db.add(db_rule)
        await self.db.flush()
        return db_rule
