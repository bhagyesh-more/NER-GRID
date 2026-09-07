"""Location & Settlement Schemas"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.schemas.common import DataOrigin, GeoJSONPoint


class LocationBase(BaseModel):
    name: str = Field(..., description="Name of town, district headquarters, chokepoint, or junction")
    state: str = Field(..., description="State (e.g. Assam, Sikkim, Meghalaya, etc.)")
    district: Optional[str] = Field(None, description="District name")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    elevation_m: Optional[float] = Field(None, description="Elevation in meters AMSL")
    location_type: str = Field(default="town", description="e.g. state_capital, district_hq, border_post, junction")


class LocationCreate(LocationBase):
    provenance_status: DataOrigin = Field(default=DataOrigin.OBSERVED)
    source_name: str = Field(default="OpenStreetMap")
    source_url: Optional[str] = None


class LocationResponse(LocationBase):
    id: str
    geometry: GeoJSONPoint
    provenance_status: DataOrigin
    source_name: str
    source_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
