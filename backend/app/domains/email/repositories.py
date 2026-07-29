from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.email.models import EmailLog

class EmailRepository:
    """
    Handles persistence logic for outbound email logs.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_quote(self, quote_id: int) -> List[EmailLog]:
        result = await self.db.execute(
            select(EmailLog)
            .where(EmailLog.quote_id == quote_id)
            .order_by(EmailLog.sent_at.desc())
        )
        return list(result.scalars().all())

    async def create_log(self, quote_id: int, recipient: str, subject: str, status: str, error_message: Optional[str] = None) -> EmailLog:
        db_log = EmailLog(
            quote_id=quote_id,
            recipient=recipient,
            subject=subject,
            status=status,
            error_message=error_message
        )
        self.db.add(db_log)
        await self.db.flush()
        return db_log
