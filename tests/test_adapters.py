"""Unit Tests for Adapters & Provenance Normalization"""
import pytest
from backend.services.ingestion.osm_adapter import OSMAdapter
from backend.services.ingestion.osrm_adapter import OSRMAdapter
from backend.services.ingestion.imd_adapter import IMDAdapter
from backend.services.ingestion.bhuvan_adapter import BhuvanAdapter
from backend.services.ingestion.ogd_adapter import OGDAdapter
from backend.schemas.common import DataOrigin


@pytest.mark.asyncio
async def test_osm_adapter_normalization():
    adapter = OSMAdapter()
    raw = await adapter.fetch_raw()
    assert len(raw) >= 5

    normalized = adapter.normalize(raw)
    assert len(normalized) >= 5

    for rec in normalized:
        assert rec["provenance_status"] == DataOrigin.OBSERVED.value
        assert "geometry_geojson" in rec
        assert "name" in rec
        assert rec["source_name"] == "OpenStreetMap"

    validated = adapter.validate_records(normalized)
    assert len(validated) > 0


def test_osrm_adapter_parsing():
    adapter = OSRMAdapter()
    # Mock realistic OSRM response structure
    mock_raw = {
        "code": "Ok",
        "routes": [
            {
                "distance": 112450.0,
                "duration": 5400.0,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[88.4354, 26.7271], [88.5283, 27.1764], [88.6138, 27.3389]],
                },
                "legs": [{"summary": "NH10"}],
            },
            {
                "distance": 125000.0,
                "duration": 6300.0,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[88.4354, 26.7271], [88.6138, 27.3389]],
                },
                "legs": [{"summary": "Via Kalimpong"}],
            },
        ],
    }

    parsed = adapter._parse_osrm_response(
        raw_data=mock_raw,
        origin_name="Siliguri",
        dest_name="Gangtok",
        origin_coords=(26.7271, 88.4354),
        dest_coords=(27.3389, 88.6138),
        source_url="https://router.project-osrm.org/test",
    )

    assert parsed["distance_km"] == 112.45
    assert parsed["duration_minutes"] == 90.0
    assert parsed["provenance_status"] == DataOrigin.PREDICTED.value
    assert len(parsed["alternatives"]) == 1
    assert parsed["alternatives"][0]["distance_km"] == 125.0


def test_imd_adapter_normalization():
    adapter = IMDAdapter()
    mock_raw = {
        "current_weather": {
            "temperature": 18.5,
            "windspeed": 3.2,
            "winddirection": 180,
            "weathercode": 2,
            "time": "2026-09-07T12:00",
        },
        "hourly": {
            "precipitation": [0.0, 1.2, 3.5, 0.5] + [0.0] * 20,
            "relativehumidity_2m": [85.0] * 24,
        },
    }

    normalized = adapter._normalize_weather_response(
        raw=mock_raw,
        lat=27.3389,
        lon=88.6138,
        location_name="Gangtok",
        source_url="https://api.open-meteo.com/v1/forecast",
    )

    assert "weather" in normalized
    assert "rainfall" in normalized
    w = normalized["weather"]
    r = normalized["rainfall"]

    assert w["temperature_c"] == 18.5
    assert w["provenance_status"] == DataOrigin.OBSERVED.value
    assert r["rainfall_mm"] == 5.2
    assert r["provenance_status"] == DataOrigin.PREDICTED.value


def test_bhuvan_adapter_catalog():
    adapter = BhuvanAdapter()
    layers = adapter.get_known_ner_layers()
    assert len(layers) >= 2
    assert any("lulc" in l["layer_name"] for l in layers)
    assert adapter.access_status == "RESTRICTED_TOKEN"


def test_ogd_adapter_catalog():
    adapter = OGDAdapter()
    catalogs = adapter.get_registered_ner_catalogs()
    assert len(catalogs) >= 2
    assert any("Rainfall" in c["title"] for c in catalogs)
