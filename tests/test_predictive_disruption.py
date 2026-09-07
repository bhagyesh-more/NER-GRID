"""Comprehensive Tests for Predictive Disruption & What-If Scenario Engine

Validates:
1. Normal conditions baseline risk calculation.
2. Increasing rainfall escalation.
3. Severe rainfall / cloudburst critical risk.
4. Simulated road closure impact.
5. Simulated landslide event impact.
6. Missing weather data graceful degradation.
7. Stale data handling & confidence deduction.
8. Low-confidence prediction detection.
9. Route recommendation flipping from Route A to Route B under scenario.
10. Simulation strictly NOT modifying observed database tables.
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.session import SessionLocal, init_db
from backend.database.models import WeatherObservationModel, RainfallObservationModel
from backend.schemas.scenario import (
    ScenarioAnalysisRequest,
    ScenarioVariableInput,
    ScenarioType,
    MissionType,
    RiskLevel,
    MissionSuitability,
)
from backend.schemas.routing import Waypoint
from ml.hazard_features import feature_store
from ml.disruption_model import disruption_model
from backend.services.scenario.service import scenario_service


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = SessionLocal()
    yield db
    db.close()


# --- TEST 1: Normal Conditions Baseline ---
def test_1_normal_conditions(db_session):
    features = {
        "key_districts": ["East Sikkim"],
        "dominant_district": "East Sikkim",
        "peak_geological_risk": 92.5,
        "precip_24h_mm": 5.0,
        "antecedent_72h_mm": 12.0,
        "rainfall_24h_ratio": 0.1,   # low fraction of threshold
        "rainfall_72h_ratio": 0.12,
        "gorge_exposure": 0.8,
    }
    res = disruption_model.calculate_disruption(features, simulated_event_penalty=0.0)
    assert res["disruption_probability"] < 45.0
    assert res["predicted_risk_level"] in (RiskLevel.LOW, RiskLevel.MEDIUM)
    assert res["confidence"] > 70.0
    assert len(res["contributing_factors"]) > 0


# --- TEST 2: Increasing Rainfall Escalation ---
def test_2_increasing_rainfall(db_session):
    features_low = {
        "key_districts": ["East Sikkim"],
        "dominant_district": "East Sikkim",
        "peak_geological_risk": 92.5,
        "precip_24h_mm": 10.0,
        "antecedent_72h_mm": 25.0,
        "rainfall_24h_ratio": 0.22,
        "rainfall_72h_ratio": 0.27,
        "gorge_exposure": 0.8,
    }
    features_high = {
        "key_districts": ["East Sikkim"],
        "dominant_district": "East Sikkim",
        "peak_geological_risk": 92.5,
        "precip_24h_mm": 48.0,  # exceeds threshold
        "antecedent_72h_mm": 110.0,
        "rainfall_24h_ratio": 1.06,
        "rainfall_72h_ratio": 1.22,
        "gorge_exposure": 0.8,
    }
    res_low = disruption_model.calculate_disruption(features_low)
    res_high = disruption_model.calculate_disruption(features_high)

    assert res_high["disruption_probability"] > res_low["disruption_probability"]
    assert res_high["predicted_risk_level"] in (RiskLevel.HIGH, RiskLevel.CRITICAL)


# --- TEST 3: Severe Rainfall / Cloudburst ---
def test_3_severe_rainfall(db_session):
    features_severe = {
        "key_districts": ["East Sikkim"],
        "dominant_district": "East Sikkim",
        "peak_geological_risk": 92.5,
        "precip_24h_mm": 115.0,  # severe deluge
        "antecedent_72h_mm": 240.0,
        "rainfall_24h_ratio": 2.55,
        "rainfall_72h_ratio": 2.66,
        "gorge_exposure": 1.0,
    }
    res = disruption_model.calculate_disruption(features_severe)
    assert res["disruption_probability"] >= 75.0
    assert res["predicted_risk_level"] == RiskLevel.CRITICAL
    assert res["mission_suitability"] == MissionSuitability.CRITICAL_AVOID


# --- TEST 4: Simulated Road Closure ---
def test_4_simulated_road_closure(db_session):
    features = {
        "key_districts": ["East Sikkim"],
        "dominant_district": "East Sikkim",
        "peak_geological_risk": 92.5,
        "precip_24h_mm": 5.0,
        "antecedent_72h_mm": 10.0,
        "rainfall_24h_ratio": 0.1,
        "rainfall_72h_ratio": 0.1,
        "gorge_exposure": 0.8,
    }
    res = disruption_model.calculate_disruption(
        features,
        simulated_event_penalty=75.0,
        simulated_event_description="Simulated rockfall and bridge closure at Rangpo",
    )
    assert res["disruption_probability"] >= 80.0
    assert res["predicted_risk_level"] == RiskLevel.CRITICAL
    assert any("Simulated" in f.factor_name for f in res["contributing_factors"])


# --- TEST 5: Simulated Landslide Event ---
def test_5_simulated_landslide(db_session):
    features = {
        "key_districts": ["Darjeeling", "East Sikkim"],
        "dominant_district": "East Sikkim",
        "peak_geological_risk": 92.5,
        "precip_24h_mm": 20.0,
        "antecedent_72h_mm": 45.0,
        "rainfall_24h_ratio": 0.44,
        "rainfall_72h_ratio": 0.5,
        "gorge_exposure": 1.0,
    }
    res = disruption_model.calculate_disruption(
        features,
        simulated_event_penalty=70.0,
        simulated_event_description="Active hill-slip between 29th Mile and Teesta Bazaar",
    )
    assert res["disruption_probability"] >= 75.0
    assert res["mission_suitability"] in (MissionSuitability.LOW, MissionSuitability.CRITICAL_AVOID)


# --- TEST 6: Missing Weather Data Graceful Degradation ---
@pytest.mark.asyncio
async def test_6_missing_weather_data(db_session):
    # Pass arbitrary coords where external weather might fail
    weather_safe = await scenario_service._get_weather_safely(db_session, "Unknown_Pass", 28.5, 95.0)
    assert "rainfall_mm" in weather_safe
    assert "temperature_c" in weather_safe
    # Model should still produce a valid calculation
    features = feature_store.extract_route_features(
        route_coords=[[95.0, 28.5], [95.1, 28.6]],
        weather_data=weather_safe,
        rainfall_data={"rainfall_mm": weather_safe["rainfall_mm"]},
    )
    res = disruption_model.calculate_disruption(features)
    assert 0.0 <= res["disruption_probability"] <= 100.0


# --- TEST 7: Stale Data Handling ---
def test_7_stale_data_handling():
    features = {
        "key_districts": ["East Sikkim"],
        "dominant_district": "East Sikkim",
        "peak_geological_risk": 92.5,
        "precip_24h_mm": 10.0,
        "antecedent_72h_mm": 20.0,
        "rainfall_24h_ratio": 0.2,
        "rainfall_72h_ratio": 0.2,
        "gorge_exposure": 0.8,
    }
    # Fresh data (0.5 hours old)
    fresh_res = disruption_model.calculate_disruption(features, data_freshness_hours=0.5)
    # Stale data (12 hours old)
    stale_res = disruption_model.calculate_disruption(features, data_freshness_hours=12.0)

    assert stale_res["confidence"] < fresh_res["confidence"]


# --- TEST 8: Low-Confidence Prediction Detection ---
def test_8_low_confidence_prediction():
    features = {
        "key_districts": [],  # sparse signal
        "dominant_district": "East Sikkim",
        "peak_geological_risk": 50.0,
        "precip_24h_mm": 0.0,
        "antecedent_72h_mm": 0.0,
        "rainfall_24h_ratio": 0.0,
        "rainfall_72h_ratio": 0.0,
        "gorge_exposure": 0.2,
    }
    # Extremely stale data (24 hours old)
    res = disruption_model.calculate_disruption(features, data_freshness_hours=24.0)
    assert res["confidence"] < 60.0
    # Provenance is maintained, confidence is distinct from disruption probability
    assert res["confidence"] != res["disruption_probability"]


# --- TEST 9: Route Recommendation Flip (Route A -> Route B) ---
@pytest.mark.asyncio
async def test_9_route_recommendation_flip(db_session):
    req_baseline = ScenarioAnalysisRequest(
        origin=Waypoint(name="Siliguri", latitude=26.7271, longitude=88.4354),
        destination=Waypoint(name="Gangtok", latitude=27.3389, longitude=88.6138),
        mission_type=MissionType.MEDICAL_EMERGENCY,
        scenario_variables=None,  # baseline
    )
    resp_baseline = await scenario_service.analyze_scenario(db_session, req_baseline)
    # Under baseline, primary Route A should be recommended (fastest)
    assert "route-primary-a" in resp_baseline.recommended_route_id

    # Now apply severe landslide/blockage scenario on NH-10 primary corridor
    req_scenario = ScenarioAnalysisRequest(
        origin=Waypoint(name="Siliguri", latitude=26.7271, longitude=88.4354),
        destination=Waypoint(name="Gangtok", latitude=27.3389, longitude=88.6138),
        mission_type=MissionType.MEDICAL_EMERGENCY,
        scenario_variables=ScenarioVariableInput(
            scenario_type=ScenarioType.LANDSLIDE_EVENT,
            blocked_location_or_corridor="NH-10 (Sevoke-Teesta)",
            rainfall_increase_mm=60.0,
        ),
    )
    resp_scenario = await scenario_service.analyze_scenario(db_session, req_scenario)

    # Under scenario, Route B must be recommended because Route A is blocked/critical
    assert "route-alternative" in resp_scenario.recommended_route_id
    assert resp_scenario.scenario_route_analysis[0].predicted_risk_level == RiskLevel.CRITICAL
    assert len(resp_scenario.early_warnings) > 0
    assert "STRONGLY RECOMMENDED" in resp_scenario.recommendation_reason


# --- TEST 10: Simulation Does NOT Modify Observed Data in DB ---
@pytest.mark.asyncio
async def test_10_simulation_does_not_modify_db(db_session):
    # Count existing observations before scenario
    w_count_before = db_session.query(WeatherObservationModel).count()
    r_count_before = db_session.query(RainfallObservationModel).count()

    req_scenario = ScenarioAnalysisRequest(
        origin=Waypoint(name="Guwahati", latitude=26.1445, longitude=91.7362),
        destination=Waypoint(name="Shillong", latitude=25.5788, longitude=91.8933),
        mission_type=MissionType.RELIEF_CONVOY,
        scenario_variables=ScenarioVariableInput(
            scenario_type=ScenarioType.CLOUDBURST,
            rainfall_increase_mm=95.0,
        ),
    )
    resp = await scenario_service.analyze_scenario(db_session, req_scenario)
    assert resp.provenance_status.value == "SIMULATED"

    # Verify counts after simulation
    w_count_after = db_session.query(WeatherObservationModel).count()
    r_count_after = db_session.query(RainfallObservationModel).count()

    # DB records MUST NOT increase due to simulated what-if events
    assert w_count_after == w_count_before
    assert r_count_after == r_count_before


# --- API Endpoint Test ---
def test_scenario_api_endpoints(client):
    # 1. GET /api/v1/scenario/types
    res_types = client.get("/api/v1/scenario/types")
    assert res_types.status_code == 200
    types_list = res_types.json()
    assert len(types_list) >= 4
    type_names = [t["type"] for t in types_list]
    assert "baseline" in type_names
    assert "heavy_rainfall" in type_names
    assert "landslide_event" in type_names

    # 2. GET /api/v1/scenario/historical-baseline
    res_hist = client.get("/api/v1/scenario/historical-baseline")
    assert res_hist.status_code == 200
    matrix = res_hist.json().get("district_hazard_matrix", {})
    assert "East Sikkim" in matrix
    assert matrix["East Sikkim"]["all_india_rank"] == 1

    # 3. POST /api/v1/scenario/analyze (Baseline)
    payload_baseline = {
        "origin": {"name": "Siliguri", "latitude": 26.7271, "longitude": 88.4354},
        "destination": {"name": "Gangtok", "latitude": 27.3389, "longitude": 88.6138},
        "mission_type": "medical_emergency",
        "scenario_variables": None,
    }
    res_analyze = client.post("/api/v1/scenario/analyze", json=payload_baseline)
    assert res_analyze.status_code == 200
    data = res_analyze.json()
    assert data["provenance_status"] == "PREDICTED"
    assert len(data["baseline_route_analysis"]) >= 1
    assert "route-primary-a" in data["recommended_route_id"]

    # 4. POST /api/v1/scenario/analyze (Simulated What-If)
    payload_sim = {
        "origin": {"name": "Siliguri", "latitude": 26.7271, "longitude": 88.4354},
        "destination": {"name": "Gangtok", "latitude": 27.3389, "longitude": 88.6138},
        "mission_type": "medical_emergency",
        "scenario_variables": {
            "scenario_type": "heavy_rainfall",
            "rainfall_increase_mm": 55.0,
            "speed_reduction_pct": 40.0,
        },
    }
    res_sim = client.post("/api/v1/scenario/analyze", json=payload_sim)
    assert res_sim.status_code == 200
    sim_data = res_sim.json()
    assert sim_data["provenance_status"] == "SIMULATED"
    assert sim_data["scenario_route_analysis"] is not None
    assert len(sim_data["early_warnings"]) > 0
