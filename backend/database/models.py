"""SQLAlchemy Database Models for NER-GRID"""
import uuid
import json
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from backend.database.session import Base
from backend.schemas.common import DataOrigin, IngestionStatus


def generate_uuid() -> str:
    return str(uuid.uuid4())


class DataSourceModel(Base):
    """Catalog of all upstream data providers with verification status."""
    __tablename__ = "data_sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    domain = Column(String(50), nullable=False, index=True)  # weather, routing, road_network, etc.
    base_url = Column(String(500), nullable=False)
    auth_type = Column(String(50), default="none")
    is_active = Column(Boolean, default=True)
    access_status = Column(String(50), default="VERIFIED")  # VERIFIED, RESTRICTED, PENDING_CREDENTIALS
    notes = Column(Text, nullable=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    weather_observations = relationship("WeatherObservationModel", back_populates="source")
    rainfall_observations = relationship("RainfallObservationModel", back_populates="source")
    routes = relationship("RouteRecordModel", back_populates="source")


class LocationModel(Base):
    """NER Settlements, checkpoints, transit hubs, and chokepoints."""
    __tablename__ = "locations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(150), nullable=False, index=True)
    state = Column(String(50), nullable=False, index=True)
    district = Column(String(100), nullable=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    elevation_m = Column(Float, nullable=True)
    location_type = Column(String(50), default="town")  # state_capital, district_hq, border_post, junction
    provenance_status = Column(String(20), default=DataOrigin.OBSERVED.value, nullable=False)
    source_name = Column(String(100), default="OpenStreetMap")
    source_url = Column(String(500), nullable=True)
    geometry_geojson = Column(Text, nullable=False)  # GeoJSON Point string
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_locations_lat_lon", "latitude", "longitude"),
        Index("idx_locations_state_district", "state", "district"),
    )

    @property
    def geometry(self):
        try:
            return json.loads(self.geometry_geojson)
        except Exception:
            return {"type": "Point", "coordinates": [self.longitude, self.latitude]}


class WeatherObservationModel(Base):
    """Real-time or forecast weather observations."""
    __tablename__ = "weather_observations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_id = Column(String(36), ForeignKey("data_sources.id"), nullable=True)
    source_name = Column(String(100), nullable=False, index=True)
    source_url = Column(String(500), nullable=True)
    station_id = Column(String(50), nullable=True, index=True)
    location_name = Column(String(150), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    temperature_c = Column(Float, nullable=True)
    wind_speed_kmh = Column(Float, nullable=True)
    wind_direction_deg = Column(Float, nullable=True)
    relative_humidity_pct = Column(Float, nullable=True)
    weather_condition = Column(String(100), nullable=True)
    observed_at = Column(DateTime, nullable=False, index=True)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    provenance_status = Column(String(20), default=DataOrigin.OBSERVED.value, nullable=False, index=True)
    confidence = Column(Float, default=1.0)
    geometry_geojson = Column(Text, nullable=False)

    source = relationship("DataSourceModel", back_populates="weather_observations")

    __table_args__ = (
        Index("idx_weather_loc_time", "location_name", "observed_at"),
        Index("idx_weather_coords", "latitude", "longitude"),
    )

    @property
    def geometry(self):
        try:
            return json.loads(self.geometry_geojson)
        except Exception:
            return {"type": "Point", "coordinates": [self.longitude, self.latitude]}


class RainfallObservationModel(Base):
    """High-priority precipitation observations and forecasts."""
    __tablename__ = "rainfall_observations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_id = Column(String(36), ForeignKey("data_sources.id"), nullable=True)
    source_name = Column(String(100), nullable=False, index=True)
    source_url = Column(String(500), nullable=True)
    station_id = Column(String(50), nullable=True, index=True)
    location_name = Column(String(150), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    rainfall_mm = Column(Float, nullable=False, index=True)
    accumulation_hours = Column(Float, default=1.0)
    observed_at = Column(DateTime, nullable=False, index=True)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    provenance_status = Column(String(20), default=DataOrigin.OBSERVED.value, nullable=False, index=True)
    confidence = Column(Float, default=1.0)
    geometry_geojson = Column(Text, nullable=False)

    source = relationship("DataSourceModel", back_populates="rainfall_observations")

    __table_args__ = (
        Index("idx_rainfall_loc_time", "location_name", "observed_at"),
        Index("idx_rainfall_coords", "latitude", "longitude"),
    )

    @property
    def geometry(self):
        try:
            return json.loads(self.geometry_geojson)
        except Exception:
            return {"type": "Point", "coordinates": [self.longitude, self.latitude]}


class RouteRecordModel(Base):
    """Computed routing paths and alternatives with real geometry."""
    __tablename__ = "routes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_id = Column(String(36), ForeignKey("data_sources.id"), nullable=True)
    provider = Column(String(50), default="OSRM", nullable=False)
    source_url = Column(String(500), nullable=True)
    origin_name = Column(String(150), nullable=False, index=True)
    destination_name = Column(String(150), nullable=False, index=True)
    origin_lat = Column(Float, nullable=False)
    origin_lon = Column(Float, nullable=False)
    dest_lat = Column(Float, nullable=False)
    dest_lon = Column(Float, nullable=False)
    distance_km = Column(Float, nullable=False)
    duration_minutes = Column(Float, nullable=False)
    geometry_geojson = Column(Text, nullable=False)  # GeoJSON LineString
    alternatives_json = Column(Text, nullable=True)   # JSON array of alternatives
    provenance_status = Column(String(20), default=DataOrigin.PREDICTED.value, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("DataSourceModel", back_populates="routes")

    @property
    def geometry(self):
        try:
            return json.loads(self.geometry_geojson)
        except Exception:
            return {"type": "LineString", "coordinates": []}

    @property
    def alternatives(self):
        try:
            return json.loads(self.alternatives_json) if self.alternatives_json else []
        except Exception:
            return []


class IngestionRunModel(Base):
    """Audit log of ingestion jobs to ensure data integrity."""
    __tablename__ = "ingestion_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_name = Column(String(100), nullable=False, index=True)
    status = Column(String(20), default=IngestionStatus.SUCCESS.value, nullable=False)
    records_ingested = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    error_log = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class IncidentReportModel(Base):
    """Field reports submitted by operators, local authorities, or crowd observers."""
    __tablename__ = "incident_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    location_name = Column(String(150), nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    report_type = Column(String(50), nullable=False, index=True)  # Road Blocked, Flooding, Landslide, Severe Traffic, etc.
    description = Column(Text, nullable=True)
    provenance_status = Column(String(20), default=DataOrigin.REPORTED.value, nullable=False)
    is_verified = Column(Boolean, default=False)
    reported_at = Column(DateTime, default=datetime.utcnow, index=True)
