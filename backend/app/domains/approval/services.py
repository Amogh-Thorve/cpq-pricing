from datetime import datetime, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.approval.repositories import ApprovalRepository
from backend.app.domains.approval.models import ApprovalRequest, ApprovalPolicy, ApprovalStatus
from backend.app.domains.approval.schemas import (
    SubmitApprovalRequest, DecideApprovalRequest, 
    ApprovalPolicyCreate, ApprovalRequestCreate
)
from backend.app.domains.quotes.services import QuoteService
from backend.app.domains.quotes.models import QuoteStatus
from backend.app.core.exceptions import EntityNotFoundError, DomainValidationError

class ApprovalService:
    """
    Business service layer managing approval cycles.
    Validates discount thresholds, routes requests to appropriate roles,
    and updates parent quote states.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.approval_repo = ApprovalRepository(db)
        self.quote_service = QuoteService(db)

    async def create_policy(self, schema: ApprovalPolicyCreate) -> ApprovalPolicy:
        return await self.approval_repo.create_policy(schema)

    async def check_and_submit_quote(self, request: SubmitApprovalRequest) -> List[ApprovalRequest]:
        """
        Evaluate if a quote triggers any active approval policies.
        If yes:
        1. Create approval request objects.
        2. Set quote status to UNDER_REVIEW.
        If no:
        1. Set quote status automatically to APPROVED.
        """
        quote = await self.quote_service.get_quote(request.quote_id)
        if quote.status != QuoteStatus.DRAFT:
            raise DomainValidationError(f"Cannot submit a quote for approval if it is in '{quote.status}' state.")

        # Calculate max discount percentage on any item or aggregate discount
        # For simplicity, check if overall discount percentage triggers policies
        total_before_discount = float(quote.total_amount) + float(quote.discount_amount)
        overall_discount = 0.0
        if total_before_discount > 0:
            overall_discount = (float(quote.discount_amount) / total_before_discount) * 100.0

        active_policies = await self.approval_repo.list_active_policies()
        triggered_requests: List[ApprovalRequest] = []

        for policy in active_policies:
            if overall_discount >= float(policy.discount_threshold):
                # Triggered! Route to role
                req = await self.approval_repo.create_request(
                    ApprovalRequestCreate(
                        quote_id=quote.id,
                        policy_id=policy.id,
                        assigned_role=policy.role_required
                    )
                )
                triggered_requests.append(req)

        if triggered_requests:
            # Quote requires review
            from backend.app.domains.quotes.schemas import QuoteUpdate
            await self.quote_service.quote_repo.update(
                quote, QuoteUpdate(status=QuoteStatus.UNDER_REVIEW)
            )
        else:
            # Auto-approved
            from backend.app.domains.quotes.schemas import QuoteUpdate
            await self.quote_service.quote_repo.update(
                quote, QuoteUpdate(status=QuoteStatus.APPROVED)
            )

        return triggered_requests

    async def decide_request(self, request_id: int, user_id: int, user_role: str, decision: DecideApprovalRequest) -> ApprovalRequest:
        """
        Record a decision (APPROVED/REJECTED) on a pending request.
        If rejected:
        - Fail the quote (status = REJECTED)
        If approved:
        - Check if all other pending approval requests for this quote are completed.
        - If all approved, mark the quote as APPROVED.
        """
        req = await self.approval_repo.get_request_by_id(request_id)
        if not req:
            raise EntityNotFoundError(f"Approval request {request_id} not found.")

        if req.status != ApprovalStatus.PENDING:
            raise DomainValidationError("This request has already been decided.")

        # Verify RBAC role match
        if user_role != req.assigned_role:
            raise DomainValidationError(f"Unauthorized. User role '{user_role}' does not match assigned role '{req.assigned_role}'.")

        # Update request state
        req.status = decision.status
        req.comments = decision.comments
        req.decided_by_id = user_id
        req.decided_at = datetime.now(timezone.utc)
        self.db.add(req)
        await self.db.flush()

        # Update parent Quote state
        quote = await self.quote_service.get_quote(req.quote_id)
        from backend.app.domains.quotes.schemas import QuoteUpdate
        
        if decision.status == ApprovalStatus.REJECTED:
            # Instantly reject the quote
            await self.quote_service.quote_repo.update(
                quote, QuoteUpdate(status=QuoteStatus.REJECTED)
            )
        elif decision.status == ApprovalStatus.APPROVED:
            # Check if all other requests for this quote are approved
            all_requests = await self.approval_repo.list_requests_for_quote(req.quote_id)
            if all(r.status == ApprovalStatus.APPROVED for r in all_requests):
                await self.quote_service.quote_repo.update(
                    quote, QuoteUpdate(status=QuoteStatus.APPROVED)
                )

        return req
