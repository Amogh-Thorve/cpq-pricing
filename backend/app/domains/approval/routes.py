from fastapi import APIRouter, Depends, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.domains.auth.routes import get_current_user
from backend.app.domains.auth.models import User
from backend.app.domains.approval.schemas import (
    ApprovalPolicyCreate, ApprovalPolicyRead, SubmitApprovalRequest,
    ApprovalRequestRead, DecideApprovalRequest
)
from backend.app.domains.approval.services import ApprovalService

router = APIRouter(prefix="/approvals", tags=["approval-workflow"])

@router.post("/policies", response_model=ApprovalPolicyRead, status_code=status.HTTP_201_CREATED)
async def create_policy(
    schema: ApprovalPolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register a new approval policy (Admin only).
    """
    service = ApprovalService(db)
    return await service.create_policy(schema)

@router.get("/policies", response_model=List[ApprovalPolicyRead])
async def list_policies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List active approval policies.
    """
    service = ApprovalService(db)
    return await service.approval_repo.list_active_policies()

@router.post("/submit", response_model=List[ApprovalRequestRead])
async def submit_quote(
    request: SubmitApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a quote for approval routing. If it triggers policies, pending tasks are created.
    """
    service = ApprovalService(db)
    return await service.check_and_submit_quote(request)

@router.get("/pending", response_model=List[ApprovalRequestRead])
async def list_pending_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List pending approval requests waiting for sign-off by the current user's role.
    """
    service = ApprovalService(db)
    return await service.approval_repo.list_pending_requests_for_role(current_user.role.value)

@router.post("/requests/{request_id}/decide", response_model=ApprovalRequestRead)
async def decide_approval_request(
    request_id: int,
    decision: DecideApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sign off or reject a pending approval request.
    """
    service = ApprovalService(db)
    return await service.decide_request(
        request_id=request_id,
        user_id=current_user.id,
        user_role=current_user.role.value,
        decision=decision
    )
