"""Rainfall Observations API Endpoints"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.schemas.weather import RainfallObservationResponse
from backend.services.weather.service import weather_service
from backend.services.gis.service import gis_service

router = APIRouter(prefix="/rainfall", tags=["Rainfall"])


@router.get("", response_model=List[RainfallObservationResponse])
def get_rainfall_observations(
    location: Optional[str] = Query(None, description="Filter by location name"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve historical/stored rainfall observations."""
    return weather_service.get_recent_rainfall(db, location_name=location, limit=limit)


@router.get("/live/{location_name}", response_model=RainfallObservationResponse)
async def get_live_rainfall_by_location(
    location_name: str,
    db: Session = Depends(get_db),
):
    """Fetch live 24-hour cumulative rainfall reading for a named NER location."""
    loc = gis_service.get_location_by_name(db, location_name)
    if not loc:
        gis_service.seed_initial_ner_locations(db)
        loc = gis_service.get_location_by_name(db, location_name)

    if not loc:
        raise HTTPException(status_code=404, detail=f"Location '{location_name}' not found in NER database.")

    try:
        res = await weather_service.get_or_fetch_weather(db, loc.name, loc.latitude, loc.longitude)
        return res["rainfall"]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Live rainfall fetch failed: {str(e)}")
