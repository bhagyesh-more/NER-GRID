"""Data Sources Catalog API Endpoints"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.database.models import DataSourceModel
from backend.schemas.ingestion import DataSourceResponse
from backend.services.ingestion import (
    OSMAdapter,
    OSRMAdapter,
    IMDAdapter,
    BhuvanAdapter,
    OGDAdapter,
)

router = APIRouter(prefix="/data-sources", tags=["Data Sources"])

INITIAL_SOURCES = [
    {
        "name": "OpenStreetMap",
        "code": "osm",
        "domain": "road_network",
        "base_url": "https://nominatim.openstreetmap.org",
        "auth_type": "none",
        "access_status": "VERIFIED",
        "notes": "Verified public endpoint for settlement geocoding and highway topology.",
    },
    {
        "name": "OSRM Routing Engine",
        "code": "osrm",
        "domain": "routing",
        "base_url": "https://router.project-osrm.org",
        "auth_type": "none",
        "access_status": "VERIFIED",
        "notes": "Verified public driving routing engine for distance, duration, and GeoJSON lines.",
    },
    {
        "name": "India Meteorological Department / Open-Meteo",
        "code": "imd",
        "domain": "weather",
        "base_url": "https://api.open-meteo.com/v1",
        "auth_type": "none",
        "access_status": "VERIFIED",
        "notes": "Real-time weather and 24h precipitation calibrated for Indian coordinates.",
    },
    {
        "name": "Bhuvan / ISRO NRSC",
        "code": "bhuvan",
        "domain": "geospatial_hazard",
        "base_url": "https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms",
        "auth_type": "bhuvan_session_token",
        "access_status": "RESTRICTED_TOKEN",
        "notes": "OGC WMS endpoints documented; raw bulk access requires departmental token.",
    },
    {
        "name": "data.gov.in (OGD India)",
        "code": "ogd",
        "domain": "government_statistics",
        "base_url": "https://api.data.gov.in",
        "auth_type": "api_key",
        "access_status": "PENDING_API_KEY",
        "notes": "Catalog metadata registered; live queries activate when DATA_GOV_IN_API_KEY is supplied.",
    },
]


@router.get("", response_model=List[DataSourceResponse])
def list_data_sources(db: Session = Depends(get_db)):
    """Retrieve catalog of all data sources with access and verification status."""
    sources = db.query(DataSourceModel).all()
    if not sources:
        # Seed initial catalog
        for s in INITIAL_SOURCES:
            existing = db.query(DataSourceModel).filter(DataSourceModel.code == s["code"]).first()
            if not existing:
                model = DataSourceModel(**s)
                db.add(model)
        db.commit()
        sources = db.query(DataSourceModel).all()
    return sources
