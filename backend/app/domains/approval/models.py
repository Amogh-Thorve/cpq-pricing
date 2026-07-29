import enum
from sqlalchemy import String, ForeignKey, Numeric, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime
from backend.app.core.database import Base

class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ApprovalPolicy(Base):
    """
    ApprovalPolicy database model.
    Establishes rules defining when quotes need to be routed for authorization
    (e.g., minimum margin or discount threshold triggers).
    """
    __tablename__ = "approval_policies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    
    # Threshold that triggers this policy (e.g. if quote discount >= threshold)
    discount_threshold: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    
    # UserRole (e.g. MANAGER, EXECUTIVE) required to sign off on this policy
    role_required: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

class ApprovalRequest(Base):
    """
    ApprovalRequest database model.
    Created when a quote triggers an active approval policy.
    """
    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    quote_id: Mapped[int] = mapped_column(ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False)
    policy_id: Mapped[int] = mapped_column(ForeignKey("approval_policies.id"), nullable=False)
    
    status: Mapped[ApprovalStatus] = mapped_column(String(50), default=ApprovalStatus.PENDING, nullable=False)
    comments: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    assigned_role: Mapped[str] = mapped_column(String(50), nullable=False)
    decided_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    policy: Mapped["ApprovalPolicy"] = relationship()
