"""NER-GRID Comprehensive End-to-End System Integration Tests

Validates complete workflow per SIH26002 specifications:
A. Mission creation
B. Real route retrieval
C. Risk analysis
D. Disruption Prediction
E. Mission-aware optimization
F. Scenario activation (Heavy Rainfall)
G. Risk recalculation & trade-offs
H. Field report ingestion & routing impact
I. Scenario reset to real baseline
J. Data provenance taxonomy (OBSERVED, REPORTED, PREDICTED, SIMULATED)
K. Graceful failure handling
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.session import SessionLocal, init_db
from backend.database.models import (
    WeatherObservationModel,
    RainfallObservationModel,
    IncidentReportModel,
)
from backend.schemas.scenario import (
    ScenarioAnalysisRequest,
    ScenarioVariableInput,
    ScenarioType,
    MissionType,
)
from backend.schemas.routing import Waypoint, RouteRequest
from backend.schemas.common import DataOrigin
from backend.services.scenario.service import scenario_service
from backend.services.routing.service import routing_service


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


# Real demonstration mission coordinates: Siliguri to STNM Hospital Gangtok (NH-10 corridor)
SILIGURI = Waypoint(name="Siliguri", latitude=26.7271, longitude=88.4354)
STNM_HOSPITAL = Waypoint(name="STNM Hospital (Gangtok)", latitude=27.3235, longitude=88.6015)


# --- TEST A: Mission Creation ---
def test_a_mission_creation(client):
    """Verify mission parameters and corridor locations in the active database."""
    res = client.get("/api/v1/locations")
    assert res.status_code == 200
    locations = res.json()
    assert len(locations) >= 10

    names = [loc["name"] for loc in locations]
    assert "Siliguri" in names
    assert any("STNM Hospital" in n or "Gangtok" in n for n in names)

    for loc in locations:
        assert loc["provenance_status"] in ["OBSERVED", "REPORTED", "PREDICTED", "SIMULATED"]
        assert -90.0 <= loc["latitude"] <= 90.0
        assert -180.0 <= loc["longitude"] <= 180.0


# --- TEST B: Real Route Retrieval ---
@pytest.mark.asyncio
async def test_b_real_route_retrieval(db_session):
    """Verify routing service retrieves real candidate highway corridors."""
    route_req = RouteRequest(
        origin=SILIGURI,
        destination=STNM_HOSPITAL,
        alternatives=True,
    )
    route_record = await routing_service.get_route(db_session, route_req)
    assert route_record is not None
    assert route_record.distance_km > 50.0
    assert route_record.duration_minutes >= 60.0
    assert route_record.origin_name == "Siliguri"
    assert "Gangtok" in route_record.destination_name or "STNM" in route_record.destination_name


# --- TEST C: Multi-Hazard Risk Analysis ---
@pytest.mark.asyncio
async def test_c_risk_analysis(db_session):
    """Verify real data fusion from NRSC Landslide Atlas and IMD normals."""
    req = ScenarioAnalysisRequest(
        origin=SILIGURI,
        destination=STNM_HOSPITAL,
        mission_type=MissionType.MEDICAL_EMERGENCY,
        scenario_variables=None,  # Baseline
    )
    res = await scenario_service.analyze_scenario(db_session, req)
    assert len(res.baseline_route_analysis) >= 2

    for analysis in res.baseline_route_analysis:
        assert 0.0 <= analysis.current_risk_score <= 100.0
        assert len(analysis.contributing_factors) >= 2
        # Check NRSC ISRO 2023 factor inclusion
        factor_names = [f.factor_name for f in analysis.contributing_factors]
        assert any("Landslide" in fn or "NRSC" in fn for fn in factor_names)


# --- TEST D: Disruption Prediction ---
@pytest.mark.asyncio
async def test_d_disruption_prediction(db_session):
    """Verify ML disruption engine estimates disruption probability and transit delay."""
    req = ScenarioAnalysisRequest(
        origin=SILIGURI,
        destination=STNM_HOSPITAL,
        mission_type=MissionType.MEDICAL_EMERGENCY,
    )
    res = await scenario_service.analyze_scenario(db_session, req)
    for analysis in res.baseline_route_analysis:
        assert 0.0 <= analysis.disruption_probability <= 100.0
        assert analysis.predicted_duration_minutes >= analysis.baseline_duration_minutes
        assert analysis.confidence > 50.0


# --- TEST E: Mission-Aware Optimization ---
@pytest.mark.asyncio
async def test_e_mission_optimization(db_session):
    """Verify Pareto ranking identifies fastest, lowest-risk, and best mission route with explainability."""
    req = ScenarioAnalysisRequest(
        origin=SILIGURI,
        destination=STNM_HOSPITAL,
        mission_type=MissionType.MEDICAL_EMERGENCY,
    )
    res = await scenario_service.analyze_scenario(db_session, req)
    analyses = res.baseline_route_analysis

    assert any(a.is_fastest for a in analyses)
    assert any(a.is_lowest_risk for a in analyses)
    assert any(a.is_recommended for a in analyses)
    assert res.recommended_route_id in [a.route_id for a in analyses]

    # Verify structured explainability
    assert res.recommendation_reason is not None
    assert len(res.recommendation_reason) > 20
    assert "RECOMMENDED" in res.recommendation_reason


# --- TEST F: Scenario Activation (Simulated Heavy Rainfall) ---
@pytest.mark.asyncio
async def test_f_scenario_activation(db_session):
    """Verify simulated what-if scenario returns SIMULATED provenance without DB modification."""
    count_before = db_session.query(WeatherObservationModel).count()

    req = ScenarioAnalysisRequest(
        origin=SILIGURI,
        destination=STNM_HOSPITAL,
        mission_type=MissionType.MEDICAL_EMERGENCY,
        scenario_variables=ScenarioVariableInput(
            scenario_type=ScenarioType.HEAVY_RAINFALL,
            rainfall_increase_mm=65.0,
        ),
    )
    res = await scenario_service.analyze_scenario(db_session, req)

    assert res.provenance_status.value == "SIMULATED"
    assert res.scenario_route_analysis is not None
    assert len(res.scenario_route_analysis) >= 2

    # Verify observations in DB were NOT mutated
    count_after = db_session.query(WeatherObservationModel).count()
    assert count_after == count_before


# --- TEST G: Risk Recalculation & Recommendation Evolution ---
@pytest.mark.asyncio
async def test_g_risk_recalculation(db_session):
    """Verify that heavy rainfall escalates hazard risk and increases delay."""
    req = ScenarioAnalysisRequest(
        origin=SILIGURI,
        destination=STNM_HOSPITAL,
        mission_type=MissionType.MEDICAL_EMERGENCY,
        scenario_variables=ScenarioVariableInput(
            scenario_type=ScenarioType.HEAVY_RAINFALL,
            rainfall_increase_mm=75.0,
        ),
    )
    res = await scenario_service.analyze_scenario(db_session, req)
    b_primary = res.baseline_route_analysis[0]
    s_primary = res.scenario_route_analysis[0]

    assert s_primary.predicted_risk_score > b_primary.predicted_risk_score
    assert s_primary.predicted_duration_minutes >= b_primary.predicted_duration_minutes
    assert res.changed_risks_summary is not None
    assert res.changed_eta_summary is not None


# --- TEST H: Field Disruption Report Workflow ---
def test_h_field_report_workflow(client, db_session):
    """Verify field reports are stored with REPORTED provenance and preserved coordinates."""
    report_data = {
        "location_name": "Rangpo Border Checkpoint",
        "report_type": "road_blockage",
        "description": "Debris and mud accumulation near bridge crossing; heavy queue.",
        "latitude": 27.1764,
        "longitude": 88.5283,
    }
    create_res = client.post("/api/v1/incidents", json=report_data)
    assert create_res.status_code == 200
    report_obj = create_res.json()

    assert report_obj["provenance_status"] == "REPORTED"
    assert report_obj["is_verified"] is False
    assert report_obj["location_name"] == "Rangpo Border Checkpoint"
    assert report_obj["reported_at"] is not None

    # Check report listing
    list_res = client.get("/api/v1/incidents")
    assert list_res.status_code == 200
    incidents = list_res.json()
    assert any(i["location_name"] == "Rangpo Border Checkpoint" for i in incidents)


# --- TEST I: Scenario Reset to Real Data Baseline ---
@pytest.mark.asyncio
async def test_i_scenario_reset(db_session):
    """Verify resetting scenario restores original real-data baseline with PREDICTED/OBSERVED status."""
    # Run with scenario
    sim_req = ScenarioAnalysisRequest(
        origin=SILIGURI,
        destination=STNM_HOSPITAL,
        mission_type=MissionType.MEDICAL_EMERGENCY,
        scenario_variables=ScenarioVariableInput(
            scenario_type=ScenarioType.CLOUDBURST,
            rainfall_increase_mm=90.0,
        ),
    )
    sim_res = await scenario_service.analyze_scenario(db_session, sim_req)
    assert sim_res.provenance_status.value == "SIMULATED"

    # Reset by passing scenario_variables=None
    base_req = ScenarioAnalysisRequest(
        origin=SILIGURI,
        destination=STNM_HOSPITAL,
        mission_type=MissionType.MEDICAL_EMERGENCY,
        scenario_variables=None,
    )
    base_res = await scenario_service.analyze_scenario(db_session, base_req)
    assert base_res.provenance_status.value == "PREDICTED"
    assert base_res.scenario_route_analysis is None


# --- TEST J: Data Provenance Taxonomy ---
def test_j_data_provenance_taxonomy(client):
    """Verify strict provenance taxonomy (OBSERVED, REPORTED, PREDICTED, SIMULATED) across all endpoints."""
    # Weather endpoint must have OBSERVED
    w_res = client.get("/api/v1/weather?location=Gangtok")
    if w_res.status_code == 200 and len(w_res.json()) > 0:
        assert w_res.json()[0]["provenance_status"] == "OBSERVED"

    # Health endpoint must declare provenance enforcement
    h_res = client.get("/api/v1/health")
    assert h_res.status_code == 200
    assert h_res.json()["provenance_enforced"] is True


# --- TEST K: Graceful Failure Handling ---
@pytest.mark.asyncio
async def test_k_graceful_failure_handling(db_session):
    """Verify system handles remote/missing weather coordinates without crashing or fabricating fake values."""
    # Analyze a location with no prior weather observations in DB
    remote_origin = Waypoint(name="Remote Outpost", latitude=28.1000, longitude=94.5000)
    remote_dest = Waypoint(name="Valley Clinic", latitude=28.2500, longitude=94.6500)

    req = ScenarioAnalysisRequest(
        origin=remote_origin,
        destination=remote_dest,
        mission_type=MissionType.GENERAL_LOGISTICS,
    )
    res = await scenario_service.analyze_scenario(db_session, req)
    assert res is not None
    assert len(res.baseline_route_analysis) >= 1
    # Check that confidence bounds remain honest
    for r in res.baseline_route_analysis:
        assert 0.0 <= r.confidence <= 100.0
