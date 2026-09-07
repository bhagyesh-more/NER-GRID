"""Data Validation Service

Ensures physical sanity, boundary checks, and integrity for all incoming geospatial & weather feeds.
"""
from datetime import datetime, timedelta
from typing import Tuple, Optional
from backend.config import settings


class ValidationError(Exception):
    pass


class GeospatialValidator:
    """Validates geographic boundaries and coordinates."""

    @staticmethod
    def validate_coordinates(lat: Optional[float], lon: Optional[float]) -> Tuple[float, float]:
        if lat is None or lon is None:
            raise ValidationError("Missing latitude or longitude coordinates.")
        if not (-90.0 <= lat <= 90.0):
            raise ValidationError(f"Invalid latitude value {lat}. Must be between -90 and 90.")
        if not (-180.0 <= lon <= 180.0):
            raise ValidationError(f"Invalid longitude value {lon}. Must be between -180 and 180.")
        return lat, lon

    @staticmethod
    def is_within_ner(lat: float, lon: float) -> bool:
        """Check if coordinates fall within the North Eastern Region bounding box."""
        return (
            settings.NER_BBOX_MIN_LAT <= lat <= settings.NER_BBOX_MAX_LAT
            and settings.NER_BBOX_MIN_LON <= lon <= settings.NER_BBOX_MAX_LON
        )

    @staticmethod
    def validate_ner_bounds(lat: float, lon: float, strict: bool = False) -> bool:
        GeospatialValidator.validate_coordinates(lat, lon)
        in_ner = GeospatialValidator.is_within_ner(lat, lon)
        if strict and not in_ner:
            raise ValidationError(
                f"Coordinates ({lat}, {lon}) fall outside the North Eastern Region bounding box "
                f"[{settings.NER_BBOX_MIN_LAT}-{settings.NER_BBOX_MAX_LAT}°N, "
                f"{settings.NER_BBOX_MIN_LON}-{settings.NER_BBOX_MAX_LON}°E]."
            )
        return in_ner


class WeatherDataValidator:
    """Validates physical meteorological limits to reject erroneous sensor telemetry."""

    @staticmethod
    def validate_temperature(temp_c: Optional[float]) -> Optional[float]:
        if temp_c is None:
            return None
        # Himalayan peaks to Assam plains reasonable bounds
        if not (-35.0 <= temp_c <= 55.0):
            raise ValidationError(f"Physically impossible temperature reading: {temp_c}°C")
        return temp_c

    @staticmethod
    def validate_rainfall(rainfall_mm: Optional[float]) -> float:
        if rainfall_mm is None:
            raise ValidationError("Rainfall measurement cannot be null.")
        if rainfall_mm < 0.0:
            raise ValidationError(f"Negative rainfall reading is invalid: {rainfall_mm} mm")
        # Extreme world record 24h rainfall (Cherrapunji record ~1000mm in 24h)
        if rainfall_mm > 1500.0:
            raise ValidationError(f"Extreme rainfall value exceeds physical thresholds: {rainfall_mm} mm")
        return rainfall_mm

    @staticmethod
    def validate_wind_speed(speed_kmh: Optional[float]) -> Optional[float]:
        if speed_kmh is None:
            return None
        if speed_kmh < 0.0 or speed_kmh > 350.0:
            raise ValidationError(f"Physically impossible wind speed reading: {speed_kmh} km/h")
        return speed_kmh

    @staticmethod
    def validate_timestamp(observed_at: datetime) -> datetime:
        now = datetime.utcnow()
        # Cannot be more than 14 days in future (allowing 14-day forecasts)
        if observed_at > now + timedelta(days=14):
            raise ValidationError(f"Observation timestamp is too far in future: {observed_at}")
        # Cannot be before 1900
        if observed_at < datetime(1900, 1, 1):
            raise ValidationError(f"Observation timestamp is invalid: {observed_at}")
        return observed_at
