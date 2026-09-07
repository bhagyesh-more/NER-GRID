"""Scenario Analysis & Predictive Disruption Schemas"""
from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.schemas.common import DataOrigin
from backend.schemas.routing import Waypoint


class MissionType(str, Enum):
    MEDICAL_EMERGENCY = "medical_emergency"
    RELIEF_CONVOY = "relief_convoy"
    HEAVY_FREIGHT = "heavy_freight"
    GENERAL_LOGISTICS = "general_logistics"


class RiskLevel(str, Enum):
    LOW = "LOW"            # 0 - 25
    MEDIUM = "MEDIUM"      # 26 - 50
    HIGH = "HIGH"          # 51 - 75
    CRITICAL = "CRITICAL"  # 76 - 100


class MissionSuitability(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    CRITICAL_AVOID = "CRITICAL_AVOID"


class ScenarioType(str, Enum):
    BASELINE = "baseline"
    HEAVY_RAINFALL = "heavy_rainfall"
    CLOUDBURST = "cloudburst"
    ROAD_BLOCKAGE = "road_blockage"
    LANDSLIDE_EVENT = "landslide_event"
    FLOOD_INUNDATION = "flood_inundation"
    MULTIPLE_DISRUPTIONS = "multiple_disruptions"


class ScenarioVariableInput(BaseModel):
    scenario_type: ScenarioType = Field(default=ScenarioType.BASELINE)
    rainfall_increase_mm: Optional[float] = Field(None, ge=0.0, description="Simulated additional rainfall in mm")
    rainfall_multiplier: Optional[float] = Field(None, ge=1.0, le=10.0, description="Multiplier for baseline rainfall")
    severe_weather_event: Optional[str] = Field(None, description="e.g. 'cloudburst', 'monsoonal_depression'")
    blocked_location_or_corridor: Optional[str] = Field(None, description="e.g. 'NH-10', 'Rangpo', 'Sevoke'")
    blocked_coordinates: Optional[List[float]] = Field(None, description="[lon, lat] coordinate to block")
    speed_reduction_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="Percentage speed reduction due to conditions")
    description: Optional[str] = None


class ContributingFactor(BaseModel):
    factor_name: str
    impact_weight: float = Field(..., ge=0.0, le=1.0, description="Normalized factor contribution")
    description: str
    signal_type: str = Field(default="meteorological", description="meteorological, geological, infrastructure, simulated")


class RouteDisruptionAnalysis(BaseModel):
    route_id: str
    route_name: str
    distance_km: float
    baseline_duration_minutes: float
    predicted_duration_minutes: float
    current_risk_score: float = Field(..., ge=0.0, le=100.0)
    predicted_risk_score: float = Field(..., ge=0.0, le=100.0)
    predicted_risk_level: RiskLevel
    disruption_probability: float = Field(..., ge=0.0, le=100.0)
    confidence: float = Field(..., ge=0.0, le=100.0)
    mission_score: float = Field(default=80.0, ge=0.0, le=100.0, description="Overall mission-weighted suitability index")
    is_fastest: bool = Field(default=False)
    is_lowest_risk: bool = Field(default=False)
    is_recommended: bool = Field(default=False)
    contributing_factors: List[ContributingFactor] = []
    mission_suitability: MissionSuitability
    expected_impact: str
    geometry: Optional[Dict[str, Any]] = None


class EarlyWarningAlert(BaseModel):
    alert_id: str
    severity: str = Field(..., description="INFO, WARNING, ALERT, CRITICAL")
    affected_route: str
    reason: str
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    recommended_action: str


class ScenarioAnalysisRequest(BaseModel):
    origin: Waypoint
    destination: Waypoint
    mission_type: MissionType = Field(default=MissionType.GENERAL_LOGISTICS)
    scenario_variables: Optional[ScenarioVariableInput] = None
    alternatives: bool = Field(default=True)


class ScenarioAnalysisResponse(BaseModel):
    prediction_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    provenance_status: DataOrigin = Field(..., description="PREDICTED for real conditions, SIMULATED for what-if")
    mission_type: MissionType
    input_sources: List[str]
    features_used: List[str]
    baseline_route_analysis: List[RouteDisruptionAnalysis]
    scenario_route_analysis: Optional[List[RouteDisruptionAnalysis]] = None
    recommended_route_id: str
    recommendation_reason: str
    changed_risks_summary: Optional[str] = None
    changed_eta_summary: Optional[str] = None
    early_warnings: List[EarlyWarningAlert] = []
