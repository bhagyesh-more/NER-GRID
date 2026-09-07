"""Data Sources and Ingestion Run Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from backend.schemas.common import IngestionStatus


class DataSourceBase(BaseModel):
    name: str
    code: str
    domain: str = Field(..., description="e.g. weather, road_network, routing, hazard, elevation")
    base_url: str
    auth_type: str = Field(default="none", description="none, api_key, oauth, institutional_restricted")
    is_active: bool = Field(default=True)
    access_status: str = Field(default="VERIFIED", description="VERIFIED, RESTRICTED, PENDING_CREDENTIALS")
    notes: Optional[str] = None


class DataSourceCreate(DataSourceBase):
    pass


class DataSourceResponse(DataSourceBase):
    id: str
    last_sync_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class IngestionRunResponse(BaseModel):
    id: str
    source_name: str
    status: IngestionStatus
    records_ingested: int
    errors_count: int
    error_log: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
