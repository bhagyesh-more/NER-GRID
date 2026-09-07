"""Predictive Disruption & Scenario What-If API Endpoints"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.schemas.scenario import (
    ScenarioAnalysisRequest,
    ScenarioAnalysisResponse,
    ScenarioType,
    MissionType,
)
from backend.services.scenario.service import scenario_service
from ml.hazard_features import feature_store

router = APIRouter(prefix="/scenario", tags=["Predictive Disruption & What-If"])


@router.post("/analyze", response_model=ScenarioAnalysisResponse)
async def analyze_scenario(
    request: ScenarioAnalysisRequest,
    db: Session = Depends(get_db),
):
    """Analyze route disruption risk under current real conditions or a simulated what-if scenario.

    - Computes real-world OSRM routes (primary + alternatives).
    - Incorporates real-time weather & 24h precipitation from IMD/Open-Meteo.
    - Fuses NRSC 2023 Landslide Atlas district susceptibility matrix.
    - If what-if scenario variables are provided, evaluates simulation in-memory without DB mutation.
    - Emits explainable contributing factors, ETA degradation, and early warnings.
    """
    try:
        response = await scenario_service.analyze_scenario(db, request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario analysis failed: {str(e)}")


@router.get("/types", response_model=List[Dict[str, Any]])
def list_scenario_types():
    """Retrieve catalog of supported what-if scenario types and parameter descriptions."""
    return [
        {
            "type": ScenarioType.BASELINE.value,
            "title": "Current Real-World Baseline",
            "description": "Uses live weather, real road geometry, and NRSC hazard baseline without perturbation.",
            "parameters": [],
        },
        {
            "type": ScenarioType.HEAVY_RAINFALL.value,
            "title": "Simulated Monsoonal Surge / Heavy Rainfall",
            "description": "Simulates elevated continuous rainfall (e.g. +40mm to +100mm) triggering soil saturation.",
            "parameters": ["rainfall_increase_mm", "rainfall_multiplier"],
        },
        {
            "type": ScenarioType.CLOUDBURST.value,
            "title": "Localized Cloudburst Event",
            "description": "Simulates extreme sudden deluge (> 85mm/h) triggering rapid debris flows in narrow mountain gorges.",
            "parameters": ["blocked_location_or_corridor"],
        },
        {
            "type": ScenarioType.ROAD_BLOCKAGE.value,
            "title": "Complete Road Severance / Chokepoint Blockage",
            "description": "Simulates a bridge collapse, rockfall, or road washout at a critical corridor junction (e.g. Rangpo on NH-10).",
            "parameters": ["blocked_location_or_corridor", "blocked_coordinates"],
        },
        {
            "type": ScenarioType.LANDSLIDE_EVENT.value,
            "title": "Slope Failure / Landslide Occurrence",
            "description": "Simulates active hill-slip cutting the primary lifeline and forcing secondary ridge diversion.",
            "parameters": ["blocked_location_or_corridor"],
        },
        {
            "type": ScenarioType.FLOOD_INUNDATION.value,
            "title": "River Inundation / Flash Flooding",
            "description": "Simulates valley floor submergence along Brahmaputra / Barak tributaries.",
            "parameters": ["speed_reduction_pct"],
        },
    ]


@router.get("/historical-baseline", response_model=Dict[str, Any])
def get_historical_baseline():
    """Retrieve authentic NRSC Landslide Atlas (ISRO 2023) district rankings and IMD monthly normals."""
    return {
        "district_hazard_matrix": feature_store.district_matrix,
        "climatology_normals": feature_store.climatology,
    }
