import enum
from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base

class PricingRuleType(str, enum.Enum):
    VOLUME_DISCOUNT = "volume_discount"
    TIERED_PRICING = "tiered_pricing"
    CUSTOMER_SEGMENT = "customer_segment"
    PROMOTIONAL = "promotional"

class PricingRule(Base):
    """
    PricingRule database model containing logic parameters.
    Saves conditions (such as minimum quantity thresholds) and discount action details.
    """
    __tablename__ = "pricing_rules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    rule_type: Mapped[PricingRuleType] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Store target validation filters (e.g. {"min_qty": 10, "product_ids": [1, 2]})
    conditions: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Store action parameters (e.g. {"discount_type": "percentage", "discount_value": 15.0})
    actions: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
