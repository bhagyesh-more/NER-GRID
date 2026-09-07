"""GIS & Location Service for NER-GRID"""
import json
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database.models import LocationModel
from backend.schemas.location import LocationCreate, LocationResponse
from backend.schemas.common import DataOrigin
from backend.services.ingestion.osm_adapter import OSMAdapter, VERIFIED_NER_SEEDS

logger = logging.getLogger(__name__)


class GISService:
    def __init__(self, osm_adapter: Optional[OSMAdapter] = None):
        self.osm_adapter = osm_adapter or OSMAdapter()

    def get_locations(
        self,
        db: Session,
        state: Optional[str] = None,
        location_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[LocationModel]:
        """Fetch locations from database with optional filters."""
        query = db.query(LocationModel)
        if state:
            query = query.filter(LocationModel.state.ilike(f"%{state}%"))
        if location_type:
            query = query.filter(LocationModel.location_type == location_type)
        return query.limit(limit).all()

    def get_location_by_name(self, db: Session, name: str) -> Optional[LocationModel]:
        return db.query(LocationModel).filter(LocationModel.name.ilike(name.strip())).first()

    def seed_initial_ner_locations(self, db: Session) -> int:
        """Seeds verified NER locations into the database if not already present."""
        count = 0
        for seed in VERIFIED_NER_SEEDS:
            existing = self.get_location_by_name(db, seed["name"])
            if not existing:
                loc = LocationModel(
                    name=seed["name"],
                    state=seed["state"],
                    district=seed.get("district"),
                    latitude=seed["lat"],
                    longitude=seed["lon"],
                    elevation_m=seed.get("elevation_m"),
                    location_type=seed.get("type", "town"),
                    provenance_status=DataOrigin.OBSERVED.value,
                    source_name="OpenStreetMap",
                    source_url="https://www.openstreetmap.org",
                    geometry_geojson=json.dumps({"type": "Point", "coordinates": [seed["lon"], seed["lat"]]}),
                )
                db.add(loc)
                count += 1
        if count > 0:
            db.commit()
            logger.info(f"Seeded {count} verified NER locations.")
        return count


gis_service = GISService()
