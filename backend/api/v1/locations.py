"""Locations & Settlements API Endpoints"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.schemas.location import LocationResponse
from backend.services.gis.service import gis_service

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get("", response_model=List[LocationResponse])
def list_locations(
    state: Optional[str] = Query(None, description="Filter by state (e.g. Sikkim, Assam, Meghalaya)"),
    location_type: Optional[str] = Query(None, description="Filter by type (e.g. state_capital, transit_hub)"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve verified settlements, transit hubs, and chokepoints in the North East."""
    # Auto-seed if empty
    locations = gis_service.get_locations(db, state=state, location_type=location_type, limit=limit)
    if not locations:
        gis_service.seed_initial_ner_locations(db)
        locations = gis_service.get_locations(db, state=state, location_type=location_type, limit=limit)
    return locations


@router.post("/seed", response_model=dict)
def seed_locations(db: Session = Depends(get_db)):
    """Seed or refresh verified ground-truth NER locations."""
    count = gis_service.seed_initial_ner_locations(db)
    return {"message": f"Seeded {count} verified NER locations."}
