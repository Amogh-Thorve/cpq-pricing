import enum
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base

class ConfigRuleType(str, enum.Enum):
    REQUIRES = "requires"       # Adding product A requires product B
    EXCLUDES = "excludes"       # Adding product A excludes/bars product B
    RECOMMENDS = "recommends"   # Adding product A suggests product B

class ConfigurationRule(Base):
    """
    ConfigurationRule database model.
    Checks and enforces business validation constraints between items in a quote.
    """
    __tablename__ = "configuration_rules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    rule_type: Mapped[ConfigRuleType] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Product triggering the rule
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    
    # Target product affected by the rule
    target_product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
