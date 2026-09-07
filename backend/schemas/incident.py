"""Incident & Field Report Schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from backend.schemas.common import DataOrigin


class IncidentReportCreate(BaseModel):
    location_name: str = Field(..., description="Location name or corridor")
    report_type: str = Field(..., description="Road Blocked, Flooding, Landslide, Severe Traffic, Accessibility Issue, Other Disruption")
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class IncidentReportResponse(BaseModel):
    id: str
    location_name: str
    report_type: str
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    provenance_status: DataOrigin = DataOrigin.REPORTED
    is_verified: bool = False
    reported_at: datetime

    model_config = {"from_attributes": True}
