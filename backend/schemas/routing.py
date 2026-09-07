"""Routing Request and Response Schemas"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.schemas.common import DataOrigin, GeoJSONLineString


class Waypoint(BaseModel):
    name: Optional[str] = None
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


class RouteRequest(BaseModel):
    origin: Waypoint
    destination: Waypoint
    waypoints: Optional[List[Waypoint]] = Field(default=[], description="Optional intermediate stops")
    alternatives: bool = Field(default=True, description="Request alternative routes if available")
    profile: str = Field(default="driving", description="driving, truck, emergency")


class RouteAlternative(BaseModel):
    route_index: int
    distance_km: float
    duration_minutes: float
    summary: Optional[str] = None
    geometry: GeoJSONLineString


class RouteResponse(BaseModel):
    id: str
    origin_name: str
    destination_name: str
    distance_km: float
    duration_minutes: float
    geometry: GeoJSONLineString
    alternatives: List[RouteAlternative] = []
    provider: str = Field(default="OSRM", description="Routing service provider")
    source_url: Optional[str] = None
    provenance_status: DataOrigin = Field(default=DataOrigin.PREDICTED)
    calculated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
