from fastapi import APIRouter, Depends, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.domains.auth.routes import get_current_user
from backend.app.domains.auth.models import User
from backend.app.domains.integrations.schemas import (
    ImportPreviewRequest, ImportPreviewResponse,
    SalesforceConnectRequest, SalesforceConnectResponse, SyncLogRead
)
from backend.app.domains.integrations.services import IntegrationService

router = APIRouter(prefix="/integrations", tags=["external-integrations"])

@router.post("/import/preview", response_model=ImportPreviewResponse)
async def generate_file_import_preview(
    request: ImportPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a sample CSV/Excel file to preview column headers, sample rows, and suggest database attribute mapping.
    """
    service = IntegrationService(db)
    return await service.generate_import_preview(request)

@router.post("/salesforce/connect", response_model=SalesforceConnectResponse)
async def connect_salesforce_crm(
    request: SalesforceConnectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Connect Salesforce CRM by trading OAuth code for refresh credentials.
    """
    service = IntegrationService(db)
    return await service.connect_salesforce(request)

@router.post("/salesforce/sync-quote/{quote_id}", response_model=SyncLogRead)
async def sync_quote_to_crm(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sync quote information and configuration items back into Salesforce CRM Opportunity line cards.
    """
    service = IntegrationService(db)
    return await service.sync_quote_to_crm(quote_id)

@router.get("/logs", response_model=List[SyncLogRead])
async def list_integration_sync_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List sync history, bulk imports, and sync audit status logs.
    """
    service = IntegrationService(db)
    return await service.integration_repo.list_sync_logs()
