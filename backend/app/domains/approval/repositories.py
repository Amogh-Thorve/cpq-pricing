from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.domains.approval.models import ApprovalPolicy, ApprovalRequest
from backend.app.domains.approval.schemas import ApprovalPolicyCreate, ApprovalPolicyUpdate, ApprovalRequestCreate

class ApprovalRepository:
    """
    Handles persistence logic for approval requests and discount limits.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_policy_by_id(self, policy_id: int) -> Optional[ApprovalPolicy]:
        result = await self.db.execute(select(ApprovalPolicy).where(ApprovalPolicy.id == policy_id))
        return result.scalars().first()

    async def list_active_policies(self) -> List[ApprovalPolicy]:
        result = await self.db.execute(
            select(ApprovalPolicy).where(ApprovalPolicy.is_active == True)
        )
        return list(result.scalars().all())

    async def create_policy(self, schema: ApprovalPolicyCreate) -> ApprovalPolicy:
        db_policy = ApprovalPolicy(**schema.model_dump())
        self.db.add(db_policy)
        await self.db.flush()
        return db_policy

    async def get_request_by_id(self, request_id: int) -> Optional[ApprovalRequest]:
        result = await self.db.execute(
            select(ApprovalRequest)
            .where(ApprovalRequest.id == request_id)
            .options(selectinload(ApprovalRequest.policy))
        )
        return result.scalars().first()

    async def list_pending_requests_for_role(self, role: str) -> List[ApprovalRequest]:
        result = await self.db.execute(
            select(ApprovalRequest)
            .where(
                ApprovalRequest.assigned_role == role,
                ApprovalRequest.status == "pending"
            )
            .options(selectinload(ApprovalRequest.policy))
        )
        return list(result.scalars().all())

    async def list_requests_for_quote(self, quote_id: int) -> List[ApprovalRequest]:
        result = await self.db.execute(
            select(ApprovalRequest)
            .where(ApprovalRequest.quote_id == quote_id)
            .options(selectinload(ApprovalRequest.policy))
        )
        return list(result.scalars().all())

    async def create_request(self, schema: ApprovalRequestCreate) -> ApprovalRequest:
        db_req = ApprovalRequest(
            quote_id=schema.quote_id,
            policy_id=schema.policy_id,
            assigned_role=schema.assigned_role
        )
        self.db.add(db_req)
        await self.db.flush()
        return db_req
