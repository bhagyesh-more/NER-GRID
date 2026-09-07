"""Weather Observations API Endpoints"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.schemas.weather import WeatherObservationResponse
from backend.services.weather.service import weather_service
from backend.services.gis.service import gis_service

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("", response_model=List[WeatherObservationResponse])
def get_weather_observations(
    location: Optional[str] = Query(None, description="Filter by location name (e.g. Gangtok, Shillong)"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve historical/cached weather observations from the database."""
    return weather_service.get_recent_weather(db, location_name=location, limit=limit)


@router.get("/live", response_model=WeatherObservationResponse)
async def get_live_weather(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude"),
    location_name: Optional[str] = Query(None, description="Optional location name"),
    db: Session = Depends(get_db),
):
    """Fetch live, real-world meteorological observation for coordinates in the North East."""
    resolved_name = location_name or f"Point ({lat:.3f}, {lon:.3f})"
    try:
        res = await weather_service.get_or_fetch_weather(db, resolved_name, lat, lon)
        return res["weather"]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Weather ingestion failed: {str(e)}")


@router.get("/live/{location_name}", response_model=WeatherObservationResponse)
async def get_live_weather_by_location(
    location_name: str,
    db: Session = Depends(get_db),
):
    """Fetch live weather for a named NER location (e.g. Gangtok, Guwahati, Shillong)."""
    loc = gis_service.get_location_by_name(db, location_name)
    if not loc:
        # Check seeds or trigger seed
        gis_service.seed_initial_ner_locations(db)
        loc = gis_service.get_location_by_name(db, location_name)

    if not loc:
        raise HTTPException(status_code=404, detail=f"Location '{location_name}' not found in NER database.")

    try:
        res = await weather_service.get_or_fetch_weather(db, loc.name, loc.latitude, loc.longitude)
        return res["weather"]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Live weather fetch failed: {str(e)}")
