"""Common Pydantic Schemas & Provenance Taxonomies"""
from enum import Enum
from datetime import datetime
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field


class DataOrigin(str, Enum):
    """Mandatory 4-tier Provenance Status for NER-GRID.

    OBSERVED: Calibrated physical instruments, AWS weather stations, satellites.
    REPORTED: Official agency bulletins (BRO, NDMA, Police, crowdsourced ground truth).
    PREDICTED: Numerical weather forecasts, hydrodynamic models, ML risk scoring.
    SIMULATED: Synthetic fixtures, stress tests, edge cases. NEVER represented as real.
    """
    OBSERVED = "OBSERVED"
    REPORTED = "REPORTED"
    PREDICTED = "PREDICTED"
    SIMULATED = "SIMULATED"


class IngestionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class GeoJSONPoint(BaseModel):
    type: str = Field(default="Point")
    coordinates: List[float] = Field(..., description="[longitude, latitude]")


class GeoJSONLineString(BaseModel):
    type: str = Field(default="LineString")
    coordinates: List[List[float]] = Field(..., description="List of [lon, lat] coordinates")


class ProvenanceMetadata(BaseModel):
    """Metadata retained for ground truth auditability."""
    source_name: str = Field(..., description="Origin agency or system (e.g. OpenStreetMap, IMD, OSRM)")
    source_url: Optional[str] = Field(None, description="Exact API endpoint or source dataset URL")
    source_type: str = Field(default="api", description="e.g. api, wms, ogd_catalog, raster_dem")
    status: DataOrigin = Field(..., description="OBSERVED, REPORTED, PREDICTED, or SIMULATED")
    observed_at: Optional[datetime] = Field(None, description="Timestamp of physical observation or forecast validity")
    ingested_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp ingested into NER-GRID")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    notes: Optional[str] = None
