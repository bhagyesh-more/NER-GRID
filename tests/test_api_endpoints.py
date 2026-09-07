"""API Integration Tests using FastAPI TestClient"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.session import init_db, SessionLocal
from backend.services.gis.service import gis_service


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["problem_statement"] == "SIH26002"
    assert data["geographic_scope"] == "North Eastern Region (NER), India"


def test_locations_endpoint(client):
    response = client.get("/api/v1/locations")
    assert response.status_code == 200
    locations = response.json()
    assert len(locations) > 0
    # Gangtok should be present
    names = [loc["name"] for loc in locations]
    assert "Gangtok" in names or "Guwahati" in names
    # Verify provenance field
    assert locations[0]["provenance_status"] == "OBSERVED"


def test_data_sources_endpoint(client):
    response = client.get("/api/v1/data-sources")
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) >= 4
    codes = [s["code"] for s in sources]
    assert "osm" in codes
    assert "osrm" in codes
    assert "imd" in codes
    assert "bhuvan" in codes


def test_ingestion_status_endpoint(client):
    response = client.get("/api/v1/ingestion/status")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_post_routes_endpoint_mock_coords(client):
    # Route between Siliguri and Gangtok
    payload = {
        "origin": {"name": "Siliguri", "latitude": 26.7271, "longitude": 88.4354},
        "destination": {"name": "Gangtok", "latitude": 27.3389, "longitude": 88.6138},
        "alternatives": True,
    }
    response = client.post("/api/v1/routes", json=payload)
    assert response.status_code == 200
    route = response.json()
    assert route["distance_km"] > 50.0
    assert route["duration_minutes"] > 30.0
    assert route["geometry"]["type"] == "LineString"
    assert len(route["geometry"]["coordinates"]) > 5
    assert route["provenance_status"] == "PREDICTED"
    assert route["provider"] == "OSRM"
