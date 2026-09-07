"""Weather and Rainfall Schemas"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from backend.schemas.common import DataOrigin, GeoJSONPoint


class WeatherObservationBase(BaseModel):
    location_name: str
    latitude: float
    longitude: float
    temperature_c: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    relative_humidity_pct: Optional[float] = None
    weather_condition: Optional[str] = None
    observed_at: datetime


class WeatherObservationCreate(WeatherObservationBase):
    station_id: Optional[str] = None
    source_name: str = Field(..., description="e.g. IMD, Open-Meteo")
    source_url: Optional[str] = None
    provenance_status: DataOrigin = Field(default=DataOrigin.OBSERVED)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class WeatherObservationResponse(WeatherObservationBase):
    id: str
    station_id: Optional[str] = None
    geometry: GeoJSONPoint
    source_name: str
    source_url: Optional[str] = None
    provenance_status: DataOrigin
    confidence: float
    ingested_at: datetime

    model_config = {"from_attributes": True}


class RainfallObservationBase(BaseModel):
    location_name: str
    latitude: float
    longitude: float
    rainfall_mm: float = Field(..., ge=0.0, description="Precipitation depth in mm")
    accumulation_hours: float = Field(default=1.0, gt=0.0, description="Accumulation window (e.g. 1h, 24h)")
    observed_at: datetime


class RainfallObservationCreate(RainfallObservationBase):
    station_id: Optional[str] = None
    source_name: str = Field(..., description="e.g. IMD, Open-Meteo, CWC")
    source_url: Optional[str] = None
    provenance_status: DataOrigin = Field(default=DataOrigin.OBSERVED)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class RainfallObservationResponse(RainfallObservationBase):
    id: str
    station_id: Optional[str] = None
    geometry: GeoJSONPoint
    source_name: str
    source_url: Optional[str] = None
    provenance_status: DataOrigin
    confidence: float
    ingested_at: datetime

    model_config = {"from_attributes": True}
