"""Unit Tests for Validation Service"""
import pytest
from datetime import datetime, timedelta
from backend.services.validation import (
    GeospatialValidator,
    WeatherDataValidator,
    ValidationError,
)


def test_valid_coordinates():
    lat, lon = GeospatialValidator.validate_coordinates(27.3389, 88.6138)
    assert lat == 27.3389
    assert lon == 88.6138


def test_invalid_coordinates():
    with pytest.raises(ValidationError):
        GeospatialValidator.validate_coordinates(95.0, 88.0)  # lat > 90

    with pytest.raises(ValidationError):
        GeospatialValidator.validate_coordinates(27.0, 195.0)  # lon > 180

    with pytest.raises(ValidationError):
        GeospatialValidator.validate_coordinates(None, 88.0)


def test_ner_bounding_box():
    # Gangtok is inside NER
    assert GeospatialValidator.is_within_ner(27.3389, 88.6138) is True
    # Guwahati is inside NER
    assert GeospatialValidator.is_within_ner(26.1445, 91.7362) is True
    # Mumbai is outside NER
    assert GeospatialValidator.is_within_ner(19.0760, 72.8777) is False
    # London is outside NER
    assert GeospatialValidator.is_within_ner(51.5074, -0.1278) is False


def test_weather_validation():
    # Valid physical readings
    assert WeatherDataValidator.validate_temperature(24.5) == 24.5
    assert WeatherDataValidator.validate_temperature(-5.0) == -5.0
    assert WeatherDataValidator.validate_rainfall(120.0) == 120.0
    assert WeatherDataValidator.validate_rainfall(0.0) == 0.0
    assert WeatherDataValidator.validate_wind_speed(45.0) == 45.0

    # Unphysical readings must raise ValidationError
    with pytest.raises(ValidationError):
        WeatherDataValidator.validate_temperature(65.0)  # impossible > 55°C

    with pytest.raises(ValidationError):
        WeatherDataValidator.validate_temperature(-50.0)  # impossible < -35°C in NER

    with pytest.raises(ValidationError):
        WeatherDataValidator.validate_rainfall(-10.0)  # negative rain

    with pytest.raises(ValidationError):
        WeatherDataValidator.validate_rainfall(2500.0)  # exceeds world records

    with pytest.raises(ValidationError):
        WeatherDataValidator.validate_wind_speed(450.0)  # extreme hurricane/tornado beyond physical


def test_timestamp_validation():
    now = datetime.utcnow()
    assert WeatherDataValidator.validate_timestamp(now) == now

    # Future beyond 14 days should fail
    far_future = now + timedelta(days=30)
    with pytest.raises(ValidationError):
        WeatherDataValidator.validate_timestamp(far_future)
