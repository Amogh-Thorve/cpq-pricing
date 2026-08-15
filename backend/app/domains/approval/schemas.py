from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from backend.app.domains.approval.models import ApprovalStatus

class ApprovalPolicyBase(BaseModel):
    name: str
    discount_threshold: float = Field(..., ge=0.0, le=100.0)
    role_required: str
    is_active: bool = True

class ApprovalPolicyCreate(ApprovalPolicyBase):
    pass

class ApprovalPolicyUpdate(BaseModel):
    name: Optional[str] = None
    discount_threshold: Optional[float] = None
    role_required: Optional[str] = None
    is_active: Optional[bool] = None

class ApprovalPolicyRead(ApprovalPolicyBase):
    id: int

    class Config:
        from_attributes = True


class ApprovalRequestBase(BaseModel):
    quote_id: int
    policy_id: int
    assigned_role: str

class ApprovalRequestCreate(ApprovalRequestBase):
    pass

class ApprovalRequestRead(ApprovalRequestBase):
    id: int
    status: ApprovalStatus
    comments: Optional[str] = None
    decided_by_id: Optional[int] = None
    created_at: datetime
    decided_at: Optional[datetime] = None
    policy: Optional[ApprovalPolicyRead] = None

    class Config:
        from_attributes = True

class SubmitApprovalRequest(BaseModel):
    quote_id: int
    comments: Optional[str] = None

class DecideApprovalRequest(BaseModel):
    status: ApprovalStatus  # APPROVED or REJECTED
    comments: Optional[str] = None
