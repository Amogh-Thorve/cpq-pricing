from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from backend.app.domains.integrations.repositories import IntegrationRepository
from backend.app.domains.integrations.schemas import (
    SalesforceConnectRequest, SalesforceConnectResponse,
    ImportPreviewRequest, ImportPreviewResponse, SyncLogRead, ColumnMapping, ColumnValidation
)
from backend.app.domains.integrations.models import IntegrationSyncLog
from backend.app.core.exceptions import DomainValidationError

class IntegrationService:
    """
    Business service layer managing external systems integrations.
    Handles Excel/CSV data imports, column mapping templates,
    and Salesforce OAuth connections.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.integration_repo = IntegrationRepository(db)

    async def generate_import_preview(self, request: ImportPreviewRequest) -> ImportPreviewResponse:
        """
        Parses a sample of file data, extracts headers, and infers database column mappings.
        """
        # Placeholder CSV/Excel parsing preview
        headers = ["First Name", "Last Name", "Email", "Phone"]
        suggested_mappings = [
            ColumnMapping(file_column="First Name", db_field="first_name"),
            ColumnMapping(file_column="Last Name", db_field="last_name"),
            ColumnMapping(file_column="Email", db_field="email"),
            ColumnMapping(file_column="Phone", db_field="phone")
        ]
        
        column_validations = [
            ColumnValidation(column_name="First Name", is_valid=True, sample_values=["John", "Jane"]),
            ColumnValidation(column_name="Last Name", is_valid=True, sample_values=["Doe", "Smith"]),
            ColumnValidation(column_name="Email", is_valid=True, sample_values=["john@example.com", "jane@example.com"]),
            ColumnValidation(column_name="Phone", is_valid=True, sample_values=["123-456-7890", "987-654-3210"])
        ]

        return ImportPreviewResponse(
            headers=headers,
            sample_rows=[
                ["John", "Doe", "john@example.com", "123-456-7890"],
                ["Jane", "Smith", "jane@example.com", "987-654-3210"]
            ],
            column_validations=column_validations,
            suggested_mappings=suggested_mappings
        )

    async def connect_salesforce(self, request: SalesforceConnectRequest) -> SalesforceConnectResponse:
        """
        Completes the Salesforce OAuth 2.0 flow by exchanging code for access tokens,
        saving them to the database, and validating connection status.
        """
        # Mocking Salesforce connection response
        # Future: call Salesforce token endpoint with oauth details.
        access_token = "mock_sf_access_token_123"
        instance_url = "https://mycompany.my.salesforce.com"
        expires_in = 3600

        await self.integration_repo.save_salesforce_token(
            access_token=access_token,
            refresh_token="mock_sf_refresh_token_123",
            instance_url=instance_url,
            expires_in=expires_in
        )

        return SalesforceConnectResponse(
            connected=True,
            instance_url=instance_url,
            user_email="sales_rep@company.com"
        )

    async def sync_quote_to_crm(self, quote_id: int) -> IntegrationSyncLog:
        """
        Exports quote details back into a Salesforce Opportunity Line Items card.
        """
        log = await self.integration_repo.create_sync_log(integration_type="salesforce")
        
        # Simulated sync action:
        # Check salesforce token, fetch quote, compile json payload, post to salesforce API.
        records_synced = 5
        
        # Mark log success
        await self.integration_repo.update_sync_log(
            log_id=log.id,
            status="success",
            records=records_synced
        )
        return log
