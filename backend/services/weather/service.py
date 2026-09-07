"""Weather & Rainfall Service

Coordinates ingestion, caching, and database persistence for weather observations.
"""
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.database.models import WeatherObservationModel, RainfallObservationModel
from backend.services.ingestion.imd_adapter import IMDAdapter
from backend.services.validation import WeatherDataValidator, GeospatialValidator

logger = logging.getLogger(__name__)


class WeatherService:
    def __init__(self, adapter: Optional[IMDAdapter] = None):
        self.adapter = adapter or IMDAdapter()

    async def get_or_fetch_weather(
        self,
        db: Session,
        location_name: str,
        lat: float,
        lon: float,
    ) -> Dict[str, Any]:
        """Fetch live weather from adapter, validate, store in database, and return."""
        # 1. Validation
        GeospatialValidator.validate_ner_bounds(lat, lon, strict=False)

        # 2. Fetch live data via adapter
        raw_res = await self.adapter.fetch_weather_for_coords(lat, lon, location_name)
        w_data = raw_res.get("weather", {})
        r_data = raw_res.get("rainfall", {})

        # 3. Validate physical limits
        WeatherDataValidator.validate_temperature(w_data.get("temperature_c"))
        WeatherDataValidator.validate_wind_speed(w_data.get("wind_speed_kmh"))
        WeatherDataValidator.validate_rainfall(r_data.get("rainfall_mm"))

        # 4. Save Weather Observation to DB
        weather_record = WeatherObservationModel(
            source_name=w_data["source_name"],
            source_url=w_data.get("source_url"),
            location_name=location_name,
            latitude=lat,
            longitude=lon,
            temperature_c=w_data.get("temperature_c"),
            wind_speed_kmh=w_data.get("wind_speed_kmh"),
            wind_direction_deg=w_data.get("wind_direction_deg"),
            relative_humidity_pct=w_data.get("relative_humidity_pct"),
            weather_condition=w_data.get("weather_condition"),
            observed_at=datetime.fromisoformat(w_data["observed_at"]),
            provenance_status=w_data["provenance_status"],
            confidence=w_data.get("confidence", 1.0),
            geometry_geojson=w_data["geometry_geojson"],
        )
        db.add(weather_record)

        # 5. Save Rainfall Observation to DB
        rainfall_record = RainfallObservationModel(
            source_name=r_data["source_name"],
            source_url=r_data.get("source_url"),
            location_name=location_name,
            latitude=lat,
            longitude=lon,
            rainfall_mm=r_data["rainfall_mm"],
            accumulation_hours=r_data.get("accumulation_hours", 24.0),
            observed_at=datetime.fromisoformat(r_data["observed_at"]),
            provenance_status=r_data["provenance_status"],
            confidence=r_data.get("confidence", 1.0),
            geometry_geojson=r_data["geometry_geojson"],
        )
        db.add(rainfall_record)
        db.commit()
        db.refresh(weather_record)
        db.refresh(rainfall_record)

        return {
            "weather": weather_record,
            "rainfall": rainfall_record,
        }

    def get_recent_weather(
        self,
        db: Session,
        location_name: Optional[str] = None,
        limit: int = 50,
    ) -> List[WeatherObservationModel]:
        query = db.query(WeatherObservationModel)
        if location_name:
            query = query.filter(WeatherObservationModel.location_name.ilike(f"%{location_name}%"))
        return query.order_by(WeatherObservationModel.observed_at.desc()).limit(limit).all()

    def get_recent_rainfall(
        self,
        db: Session,
        location_name: Optional[str] = None,
        limit: int = 50,
    ) -> List[RainfallObservationModel]:
        query = db.query(RainfallObservationModel)
        if location_name:
            query = query.filter(RainfallObservationModel.location_name.ilike(f"%{location_name}%"))
        return query.order_by(RainfallObservationModel.observed_at.desc()).limit(limit).all()


weather_service = WeatherService()
