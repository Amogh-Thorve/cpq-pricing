from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, List
from datetime import datetime

class SyncLogRead(BaseModel):
    id: int
    integration_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    records_processed: int
    error_summary: Optional[str] = None

    class Config:
        from_attributes = True

class SalesforceConnectRequest(BaseModel):
    code: str

class SalesforceConnectResponse(BaseModel):
    connected: bool
    instance_url: str
    user_email: Optional[str] = None

class ColumnMapping(BaseModel):
    file_column: str
    db_field: str

class ImportPreviewRequest(BaseModel):
    file_name: str
    content_type: str  # csv, xlsx
    raw_data: str      # Base64 encoded sample content

class ColumnValidation(BaseModel):
    column_name: str
    is_valid: bool
    sample_values: List[str] = []

class ImportPreviewResponse(BaseModel):
    headers: List[str] = []
    sample_rows: List[List[str]] = []
    column_validations: List[ColumnValidation] = []
    suggested_mappings: List[ColumnMapping] = []
