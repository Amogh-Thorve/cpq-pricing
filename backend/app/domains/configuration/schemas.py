from pydantic import BaseModel
from typing import Optional, List
from backend.app.domains.configuration.models import ConfigRuleType

class ConfigurationRuleBase(BaseModel):
    name: str
    rule_type: ConfigRuleType
    is_active: bool = True
    product_id: int
    target_product_id: int

class ConfigurationRuleCreate(ConfigurationRuleBase):
    pass

class ConfigurationRuleUpdate(BaseModel):
    name: Optional[str] = None
    rule_type: Optional[ConfigRuleType] = None
    is_active: Optional[bool] = None
    product_id: Optional[int] = None
    target_product_id: Optional[int] = None

class ConfigurationRuleRead(ConfigurationRuleBase):
    id: int

    class Config:
        from_attributes = True

class ValidateConfigurationRequest(BaseModel):
    product_ids: List[int]

class ConfigurationErrorDetail(BaseModel):
    rule_id: int
    rule_name: str
    rule_type: ConfigRuleType
    message: str

class ValidateConfigurationResponse(BaseModel):
    is_valid: bool
    errors: List[ConfigurationErrorDetail] = []
    recommendations: List[str] = []
