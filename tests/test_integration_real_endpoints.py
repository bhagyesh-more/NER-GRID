"""Integration Test against Live Public Endpoints

Proves real-world data retrieval from OSRM and calibrated weather feeds.
"""
import pytest
from backend.services.ingestion.osrm_adapter import OSRMAdapter
from backend.services.ingestion.imd_adapter import IMDAdapter
from backend.schemas.common import DataOrigin


@pytest.mark.asyncio
async def test_live_osrm_routing_siliguri_to_gangtok():
    adapter = OSRMAdapter()
    # Siliguri: 26.7271, 88.4354 -> Gangtok: 27.3389, 88.6138
    res = await adapter.calculate_route(
        origin_lat=26.7271,
        origin_lon=88.4354,
        dest_lat=27.3389,
        dest_lon=88.6138,
        origin_name="Siliguri",
        dest_name="Gangtok",
        alternatives=True,
    )

    assert res["distance_km"] > 80.0
    assert res["duration_minutes"] > 45.0
    assert res["geometry"]["type"] == "LineString"
    assert len(res["geometry"]["coordinates"]) > 50
    assert res["provenance_status"] == DataOrigin.PREDICTED.value
    assert "https://" in res["source_url"]


@pytest.mark.asyncio
async def test_live_weather_ingestion_gangtok():
    adapter = IMDAdapter()
    res = await adapter.fetch_weather_for_coords(
        lat=27.3389,
        lon=88.6138,
        location_name="Gangtok",
    )

    w = res["weather"]
    r = res["rainfall"]

    # Validate authentic physical variables
    assert -10.0 <= w["temperature_c"] <= 45.0
    assert 0.0 <= w["wind_speed_kmh"] <= 150.0
    assert r["rainfall_mm"] >= 0.0
    assert w["provenance_status"] == DataOrigin.OBSERVED.value
    assert r["provenance_status"] == DataOrigin.PREDICTED.value
