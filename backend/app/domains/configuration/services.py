from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.configuration.repositories import ConfigurationRuleRepository
from backend.app.domains.configuration.schemas import (
    ValidateConfigurationRequest, ValidateConfigurationResponse, 
    ConfigurationErrorDetail, ConfigurationRuleCreate, ConfigurationRuleUpdate
)
from backend.app.domains.configuration.models import ConfigurationRule, ConfigRuleType
from backend.app.core.exceptions import EntityNotFoundError

class ConfigurationService:
    """
    Business service layer managing validation rules for complex product bundles.
    Ensures that customer choices satisfy dependency and exclusivity matrices.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.config_repo = ConfigurationRuleRepository(db)

    async def create_rule(self, schema: ConfigurationRuleCreate) -> ConfigurationRule:
        """
        Create a new product validation rule.
        """
        return await self.config_repo.create(schema)

    async def get_rule(self, rule_id: int) -> ConfigurationRule:
        rule = await self.config_repo.get_by_id(rule_id)
        if not rule:
            raise EntityNotFoundError(f"Configuration rule {rule_id} not found.")
        return rule

    async def validate_selected_products(self, request: ValidateConfigurationRequest) -> ValidateConfigurationResponse:
        """
        Runs validation checks on a set of selected product IDs.
        Checks for:
        1. Required dependencies (e.g. A requires B, if A is selected, B must be selected too).
        2. Mutually exclusive items (e.g. A excludes B, if A is selected, B cannot be selected).
        """
        selected_set = set(request.product_ids)
        triggered_rules = await self.config_repo.get_rules_for_products(request.product_ids)
        
        errors: List[ConfigurationErrorDetail] = []
        recommendations: List[str] = []
        is_valid = True

        for rule in triggered_rules:
            # 1. Enforce REQUIRES dependency check
            if rule.rule_type == ConfigRuleType.REQUIRES:
                if rule.target_product_id not in selected_set:
                    is_valid = False
                    errors.append(
                        ConfigurationErrorDetail(
                            rule_id=rule.id,
                            rule_name=rule.name,
                            rule_type=rule.rule_type,
                            message=f"Product ID {rule.product_id} requires Product ID {rule.target_product_id} to be configured."
                        )
                    )

            # 2. Enforce EXCLUDES exclusion check
            elif rule.rule_type == ConfigRuleType.EXCLUDES:
                if rule.target_product_id in selected_set:
                    is_valid = False
                    errors.append(
                        ConfigurationErrorDetail(
                            rule_id=rule.id,
                            rule_name=rule.name,
                            rule_type=rule.rule_type,
                            message=f"Product ID {rule.product_id} cannot be combined with Product ID {rule.target_product_id}."
                        )
                    )

            # 3. Handle RECOMMENDS recommendations check
            elif rule.rule_type == ConfigRuleType.RECOMMENDS:
                if rule.target_product_id not in selected_set:
                    recommendations.append(
                        f"Based on selection of Product ID {rule.product_id}, we recommend adding Product ID {rule.target_product_id}."
                    )

        return ValidateConfigurationResponse(
            is_valid=is_valid,
            errors=errors,
            recommendations=recommendations
        )
