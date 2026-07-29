from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from backend.app.domains.integrations.models import IntegrationSyncLog, SalesforceToken

class IntegrationRepository:
    """
    Handles database logic for integration states, log history, and OAuth tokens.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_sync_logs(self, limit: int = 50) -> List[IntegrationSyncLog]:
        result = await self.db.execute(
            select(IntegrationSyncLog)
            .order_by(IntegrationSyncLog.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_sync_log(self, integration_type: str) -> IntegrationSyncLog:
        db_log = IntegrationSyncLog(
            integration_type=integration_type,
            status="running"
        )
        self.db.add(db_log)
        await self.db.flush()
        return db_log

    async def update_sync_log(self, log_id: int, status: str, records: int, error_summary: Optional[str] = None) -> IntegrationSyncLog:
        result = await self.db.execute(select(IntegrationSyncLog).where(IntegrationSyncLog.id == log_id))
        db_log = result.scalars().first()
        if db_log:
            db_log.status = status
            db_log.records_processed = records
            db_log.completed_at = func.now() if hasattr(func, 'now') else datetime.utcnow()
            db_log.error_summary = error_summary
            self.db.add(db_log)
            await self.db.flush()
        return db_log

    async def save_salesforce_token(self, access_token: str, refresh_token: Optional[str], instance_url: str, expires_in: int) -> SalesforceToken:
        # Clear previous tokens to keep single reference active
        from sqlalchemy import delete
        await self.db.execute(delete(SalesforceToken))
        await self.db.flush()

        db_token = SalesforceToken(
            access_token=access_token,
            refresh_token=refresh_token,
            instance_url=instance_url,
            expires_in=expires_in
        )
        self.db.add(db_token)
        await self.db.flush()
        return db_token

    async def get_salesforce_token(self) -> Optional[SalesforceToken]:
        result = await self.db.execute(select(SalesforceToken).limit(1))
        return result.scalars().first()
