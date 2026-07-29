from fastapi import APIRouter, Depends, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.domains.auth.routes import get_current_user
from backend.app.domains.auth.models import User
from backend.app.domains.configuration.schemas import (
    ValidateConfigurationRequest, ValidateConfigurationResponse,
    ConfigurationRuleCreate, ConfigurationRuleRead
)
from backend.app.domains.configuration.services import ConfigurationService

router = APIRouter(prefix="/configuration", tags=["configuration-engine"])

@router.post("/validate", response_model=ValidateConfigurationResponse)
async def validate_configuration(
    request: ValidateConfigurationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate product compatibility and dependency rules for a set of selected product IDs.
    """
    service = ConfigurationService(db)
    return await service.validate_selected_products(request)

@router.post("/rules", response_model=ConfigurationRuleRead, status_code=status.HTTP_201_CREATED)
async def create_rule(
    schema: ConfigurationRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new product compatibility/dependency rule.
    """
    service = ConfigurationService(db)
    return await service.create_rule(schema)

@router.get("/rules", response_model=List[ConfigurationRuleRead])
async def list_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all configuration compatibility rules.
    """
    service = ConfigurationService(db)
    return await service.config_repo.list_active()
