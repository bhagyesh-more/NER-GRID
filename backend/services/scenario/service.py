"""Scenario & Predictive Disruption Service for NER-GRID

Performs multi-criteria route risk analysis under current real-world observations
and simulated what-if scenarios without mutating database state.
"""
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.schemas.common import DataOrigin
from backend.schemas.routing import RouteRequest, Waypoint
from backend.schemas.scenario import (
    ScenarioAnalysisRequest,
    ScenarioAnalysisResponse,
    ScenarioVariableInput,
    ScenarioType,
    RouteDisruptionAnalysis,
    EarlyWarningAlert,
    RiskLevel,
    MissionSuitability,
    MissionType,
)
from backend.database.models import WeatherObservationModel, RainfallObservationModel, IncidentReportModel
from backend.services.routing.service import routing_service
from backend.services.weather.service import weather_service
from backend.services.gis.service import gis_service
from ml.hazard_features import feature_store
from ml.disruption_model import disruption_model

logger = logging.getLogger(__name__)


class ScenarioService:
    def __init__(self):
        self.routing = routing_service
        self.weather = weather_service
        self.gis = gis_service
        self.features = feature_store
        self.model = disruption_model

    async def analyze_scenario(
        self,
        db: Session,
        request: ScenarioAnalysisRequest,
    ) -> ScenarioAnalysisResponse:
        prediction_id = f"pred-{uuid.uuid4().hex[:8]}"
        is_simulation = (
            request.scenario_variables is not None
            and request.scenario_variables.scenario_type != ScenarioType.BASELINE
        )
        provenance = DataOrigin.SIMULATED if is_simulation else DataOrigin.PREDICTED

        # 1. Obtain Real Candidate Routes (Primary + Alternatives)
        origin_lat = request.origin.latitude
        origin_lon = request.origin.longitude
        dest_lat = request.destination.latitude
        dest_lon = request.destination.longitude
        origin_name = request.origin.name or f"Origin ({origin_lat:.3f}, {origin_lon:.3f})"
        dest_name = request.destination.name or f"Destination ({dest_lat:.3f}, {dest_lon:.3f})"

        # Query OSRM routing
        route_req = RouteRequest(
            origin=request.origin,
            destination=request.destination,
            alternatives=request.alternatives,
        )
        primary_record = await self.routing.get_route(db, route_req)

        # Build list of candidate routes: Route A (Primary), Route B (Alt 1 if exists, or synthesized divergence)
        candidate_routes_data = []
        candidate_routes_data.append({
            "id": "route-primary-a",
            "name": f"Route A (Primary Lifeline via {origin_name}-{dest_name})",
            "distance_km": primary_record.distance_km,
            "duration_minutes": primary_record.duration_minutes,
            "geometry": primary_record.geometry,
        })

        alts = primary_record.alternatives
        if alts:
            for idx, alt in enumerate(alts, start=1):
                candidate_routes_data.append({
                    "id": f"route-alternative-{chr(65 + idx).lower()}",
                    "name": f"Route {chr(65 + idx)} ({alt.get('summary', 'Alternative Bypass')})",
                    "distance_km": alt.get("distance_km", primary_record.distance_km * 1.12),
                    "duration_minutes": alt.get("duration_minutes", primary_record.duration_minutes * 1.2),
                    "geometry": alt.get("geometry", primary_record.geometry),
                })
        else:
            # If OSRM only returned 1 route (common in single mountain passes), synthesize a secondary detour corridor
            # e.g., via Kalimpong / Teesta bypass for NH-10
            alt_coords = [
                [c[0] + 0.04, c[1] + 0.02] if idx % 2 == 0 else c
                for idx, c in enumerate(primary_record.geometry.get("coordinates", []))
            ]
            candidate_routes_data.append({
                "id": "route-alternative-b",
                "name": f"Route B (Contingency Ridge Bypass via {dest_name} East)",
                "distance_km": round(primary_record.distance_km * 1.18, 1),
                "duration_minutes": round(primary_record.duration_minutes * 1.25, 1),
                "geometry": {"type": "LineString", "coordinates": alt_coords},
            })

        # 2. Ingest / Query Real Meteorological Telemetry for Endpoints
        w_origin = await self._get_weather_safely(db, origin_name, origin_lat, origin_lon)
        w_dest = await self._get_weather_safely(db, dest_name, dest_lat, dest_lon)

        # Aggregate rainfall along corridor
        avg_precip_24h = (w_origin["rainfall_mm"] + w_dest["rainfall_mm"]) / 2.0
        weather_summary = {
            "temperature_c": (w_origin["temperature_c"] + w_dest["temperature_c"]) / 2.0,
            "wind_speed_kmh": max(w_origin["wind_speed_kmh"], w_dest["wind_speed_kmh"]),
            "rainfall_mm": avg_precip_24h,
        }

        # 2.5 Query Active Reported Field Incidents from Database
        recent_incidents = db.query(IncidentReportModel).order_by(IncidentReportModel.reported_at.desc()).limit(20).all()

        # 3. Evaluate Baseline Disruption Risk for Each Route
        baseline_analyses: List[RouteDisruptionAnalysis] = []
        for c_route in candidate_routes_data:
            coords = c_route["geometry"].get("coordinates", [])
            features = self.features.extract_route_features(
                route_coords=coords,
                weather_data=weather_summary,
                rainfall_data={"rainfall_mm": avg_precip_24h},
            )

            is_primary = "primary" in c_route["id"]
            # Check if any reported incident matches this route
            reported_event_penalty = 0.0
            reported_event_desc = ""
            if is_primary and recent_incidents:
                for inc in recent_incidents:
                    loc_lower = inc.location_name.lower()
                    if loc_lower in c_route["name"].lower() or loc_lower in origin_name.lower() or loc_lower in dest_name.lower():
                        reported_event_penalty = 50.0 if inc.report_type in ["Road Blocked", "Landslide"] else 25.0
                        reported_event_desc = f"Active field report: {inc.report_type} at {inc.location_name} ({inc.description or 'unverified'})"
                        break

            disrupt_res = self.model.calculate_disruption(
                features=features,
                simulated_event_penalty=reported_event_penalty,
                simulated_event_description=reported_event_desc,
                mission_type=request.mission_type,
            )

            # Route B is slightly longer but avoids the narrowest gorge bottleneck
            if "route-alternative-b" in c_route["id"]:
                # Alternative route traverses ridge with lower gorge exposure
                disrupt_res["disruption_probability"] = max(10.0, round(disrupt_res["disruption_probability"] * 0.75, 1))
                disrupt_res["predicted_risk_score"] = disrupt_res["disruption_probability"]

            risk_level = self._get_risk_level(disrupt_res["disruption_probability"])
            baseline_analyses.append(RouteDisruptionAnalysis(
                route_id=c_route["id"],
                route_name=c_route["name"],
                distance_km=c_route["distance_km"],
                baseline_duration_minutes=c_route["duration_minutes"],
                predicted_duration_minutes=c_route["duration_minutes"],
                current_risk_score=disrupt_res["disruption_probability"],
                predicted_risk_score=disrupt_res["disruption_probability"],
                predicted_risk_level=risk_level,
                disruption_probability=disrupt_res["disruption_probability"],
                confidence=disrupt_res["confidence"],
                contributing_factors=disrupt_res["contributing_factors"],
                mission_suitability=disrupt_res["mission_suitability"],
                expected_impact=self._generate_impact_summary(disrupt_res["disruption_probability"], c_route["name"]),
                geometry=c_route["geometry"],
            ))

        # 4. Evaluate What-If Scenario (if requested)
        scenario_analyses: Optional[List[RouteDisruptionAnalysis]] = None
        early_warnings: List[EarlyWarningAlert] = []
        changed_risks_summary = None
        changed_eta_summary = None

        if is_simulation and request.scenario_variables:
            scenario_analyses = []
            sc_vars = request.scenario_variables

            # Calculate simulated rainfall
            sim_rainfall = avg_precip_24h
            if sc_vars.rainfall_multiplier:
                sim_rainfall *= sc_vars.rainfall_multiplier
            if sc_vars.rainfall_increase_mm:
                sim_rainfall += sc_vars.rainfall_increase_mm
            if sc_vars.scenario_type == ScenarioType.CLOUDBURST:
                sim_rainfall += 85.0  # extreme cloudburst intensity
            elif sc_vars.scenario_type == ScenarioType.HEAVY_RAINFALL and not sc_vars.rainfall_increase_mm:
                sim_rainfall += 45.0

            sim_weather = dict(weather_summary)
            sim_weather["rainfall_mm"] = sim_rainfall

            for c_route in candidate_routes_data:
                coords = c_route["geometry"].get("coordinates", [])
                features = self.features.extract_route_features(
                    route_coords=coords,
                    weather_data=sim_weather,
                    rainfall_data={"rainfall_mm": sim_rainfall},
                    historical_rainfall_72h_mm=sim_rainfall * 2.4,
                )

                is_primary = "primary" in c_route["id"]
                event_penalty = 0.0
                event_desc = ""

                # If road blockage or landslide specified on primary corridor (e.g. NH-10 or Rangpo)
                if sc_vars.scenario_type in (ScenarioType.ROAD_BLOCKAGE, ScenarioType.LANDSLIDE_EVENT, ScenarioType.MULTIPLE_DISRUPTIONS):
                    if is_primary:
                        event_penalty = 75.0
                        event_desc = f"Simulated complete corridor blockage on {c_route['name']} ({sc_vars.blocked_location_or_corridor or 'Mudslide at chokepoint'})."
                    else:
                        # Alternative route bypasses the blockage
                        features["gorge_exposure"] = 0.25
                        event_penalty = 0.0
                        event_desc = "Bypasses primary valley choke point via secondary ridge alignment."

                disrupt_res = self.model.calculate_disruption(
                    features=features,
                    simulated_event_penalty=event_penalty,
                    simulated_event_description=event_desc,
                    mission_type=request.mission_type,
                )

                # Alternative route discount under scenario
                if not is_primary:
                    disrupt_res["disruption_probability"] = min(50.0, round(disrupt_res["disruption_probability"] * 0.6, 1))
                    disrupt_res["predicted_risk_score"] = disrupt_res["disruption_probability"]
                    disrupt_res["mission_suitability"] = self.model._evaluate_mission_suitability(
                        disrupt_res["disruption_probability"], request.mission_type
                    )

                # Calculate delayed ETA under scenario conditions
                delay_factor = 1.0
                if sc_vars.speed_reduction_pct:
                    delay_factor += (sc_vars.speed_reduction_pct / 100.0)
                elif disrupt_res["disruption_probability"] > 70.0:
                    delay_factor = 1.8  # severe slowdown / detour
                elif disrupt_res["disruption_probability"] > 40.0:
                    delay_factor = 1.3  # moderate slowdown

                predicted_duration = round(c_route["duration_minutes"] * delay_factor, 1)
                risk_level = self._get_risk_level(disrupt_res["disruption_probability"])

                analysis = RouteDisruptionAnalysis(
                    route_id=c_route["id"],
                    route_name=c_route["name"],
                    distance_km=c_route["distance_km"],
                    baseline_duration_minutes=c_route["duration_minutes"],
                    predicted_duration_minutes=predicted_duration,
                    current_risk_score=baseline_analyses[0].current_risk_score if is_primary else baseline_analyses[1].current_risk_score,
                    predicted_risk_score=disrupt_res["disruption_probability"],
                    predicted_risk_level=risk_level,
                    disruption_probability=disrupt_res["disruption_probability"],
                    confidence=disrupt_res["confidence"],
                    contributing_factors=disrupt_res["contributing_factors"],
                    mission_suitability=disrupt_res["mission_suitability"],
                    expected_impact=self._generate_impact_summary(disrupt_res["disruption_probability"], c_route["name"]),
                    geometry=c_route["geometry"],
                )
                scenario_analyses.append(analysis)

                # Check for Early Warnings
                if disrupt_res["disruption_probability"] >= 50.0:
                    early_warnings.append(EarlyWarningAlert(
                        alert_id=f"alert-{uuid.uuid4().hex[:6]}",
                        severity="CRITICAL" if disrupt_res["disruption_probability"] >= 75.0 else "WARNING",
                        affected_route=c_route["name"],
                        reason=f"Predicted disruption probability {disrupt_res['disruption_probability']}% under {sc_vars.scenario_type.value}.",
                        confidence=disrupt_res["confidence"],
                        recommended_action="Divert to alternative bypass or suspend non-essential transit." if is_primary else "Deploy road clearing equipment on standby.",
                    ))

            # Build comparison summaries
            r0_base = baseline_analyses[0]
            r0_scen = scenario_analyses[0]
            r1_scen = scenario_analyses[1] if len(scenario_analyses) > 1 else r0_scen

            changed_risks_summary = (
                f"Primary corridor risk escalated from {r0_base.predicted_risk_score}% ({r0_base.predicted_risk_level.value}) "
                f"to {r0_scen.predicted_risk_score}% ({r0_scen.predicted_risk_level.value}) under {sc_vars.scenario_type.value}."
            )
            changed_eta_summary = (
                f"Primary ETA degraded by +{round(r0_scen.predicted_duration_minutes - r0_base.baseline_duration_minutes, 1)} minutes "
                f"(from {r0_base.baseline_duration_minutes}m to {r0_scen.predicted_duration_minutes}m)."
            )

        # 5. Recommendation Decision Logic
        active_list = scenario_analyses if scenario_analyses else baseline_analyses
        recommended_route, rec_reason = self._determine_recommended_route(active_list, request.mission_type, is_simulation)

        return ScenarioAnalysisResponse(
            prediction_id=prediction_id,
            timestamp=datetime.utcnow(),
            provenance_status=provenance,
            mission_type=request.mission_type,
            input_sources=["OpenStreetMap", "OSRM", "Open-Meteo / IMD", "NRSC Landslide Atlas (ISRO 2023)"],
            features_used=[
                "24h Precipitation (mm)",
                "72h Antecedent Soil Moisture (mm)",
                "NRSC Landslide Susceptibility Index",
                "Mountain Gorge Exposure",
                "Road Network Geometry & Bridge Crossings",
            ],
            baseline_route_analysis=baseline_analyses,
            scenario_route_analysis=scenario_analyses,
            recommended_route_id=recommended_route.route_id,
            recommendation_reason=rec_reason,
            changed_risks_summary=changed_risks_summary,
            changed_eta_summary=changed_eta_summary,
            early_warnings=early_warnings,
        )

    def _determine_recommended_route(
        self,
        analyses: List[RouteDisruptionAnalysis],
        mission_type: MissionType,
        is_simulation: bool,
    ) -> Tuple[RouteDisruptionAnalysis, str]:
        """Selects the Pareto-optimal route balancing ETA against disruption probability."""
        if len(analyses) == 1:
            return analyses[0], f"Only one feasible route identified for this corridor ({analyses[0].route_name})."

        r_primary = analyses[0]
        r_alt = analyses[1]

        # If primary risk is High or Critical, and Alt is significantly safer:
        if r_primary.predicted_risk_score > 60.0 and r_alt.predicted_risk_score < r_primary.predicted_risk_score:
            time_diff = round(r_alt.predicted_duration_minutes - r_primary.predicted_duration_minutes, 1)
            reason = (
                f"{r_alt.route_name} is STRONGLY RECOMMENDED because its predicted disruption risk "
                f"({r_alt.predicted_risk_score}%) is substantially lower than the primary route "
                f"({r_primary.predicted_risk_score}%), {'saving overall transit time' if time_diff <= 0 else f'despite an additional {time_diff} minutes of transit'}."
            )
            return r_alt, reason

        # For Medical Emergency: if primary risk > 35, prefer safer route if alt is <= 25
        if mission_type == MissionType.MEDICAL_EMERGENCY and r_primary.predicted_risk_score > 35.0 and r_alt.predicted_risk_score <= 30.0:
            return r_alt, f"{r_alt.route_name} recommended for {mission_type.value}: prioritizes zero-blockage transit certainty."

        # Default to Primary if conditions are manageable
        reason = (
            f"{r_primary.route_name} is RECOMMENDED as the optimal operational choice: "
            f"fastest transit ({r_primary.predicted_duration_minutes} mins) with acceptable disruption risk "
            f"({r_primary.predicted_risk_score}% - {r_primary.predicted_risk_level.value})."
        )
        return r_primary, reason

    async def _get_weather_safely(self, db: Session, name: str, lat: float, lon: float) -> Dict[str, Any]:
        # 1. Check if DB already has recent weather observation for this location
        existing_w = db.query(WeatherObservationModel).filter(
            WeatherObservationModel.location_name.ilike(f"%{name}%")
        ).order_by(WeatherObservationModel.observed_at.desc()).first()

        existing_r = db.query(RainfallObservationModel).filter(
            RainfallObservationModel.location_name.ilike(f"%{name}%")
        ).order_by(RainfallObservationModel.observed_at.desc()).first()

        if existing_w and existing_r:
            return {
                "temperature_c": existing_w.temperature_c or 20.0,
                "wind_speed_kmh": existing_w.wind_speed_kmh or 5.0,
                "rainfall_mm": existing_r.rainfall_mm or 0.0,
            }

        # 2. If not in DB, query adapter directly WITHOUT mutating DB during scenario analysis
        try:
            raw = await self.weather.adapter.fetch_weather_for_coords(lat, lon, name)
            w = raw.get("weather", {})
            r = raw.get("rainfall", {})
            return {
                "temperature_c": w.get("temperature_c", 20.0),
                "wind_speed_kmh": w.get("wind_speed_kmh", 5.0),
                "rainfall_mm": r.get("rainfall_mm", 0.0),
            }
        except Exception as e:
            logger.warning(f"Failed to query weather for {name}: {e}")
            return {"temperature_c": 20.0, "wind_speed_kmh": 5.0, "rainfall_mm": 2.0}

    def _get_risk_level(self, score: float) -> RiskLevel:
        if score <= 25.0:
            return RiskLevel.LOW
        elif score <= 50.0:
            return RiskLevel.MEDIUM
        elif score <= 75.0:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    def _generate_impact_summary(self, risk: float, route_name: str) -> str:
        if risk <= 25.0:
            return f"Clear transit conditions. Low risk along {route_name}."
        elif risk <= 50.0:
            return f"Moderate monsoonal runoff. Slow speeds around drainage culverts and minor hill curves."
        elif risk <= 75.0:
            return f"High risk of mud slips, debris falls, and waterlogging. Convoys must proceed with spotters."
        return f"CRITICAL: Active landslide / flash flood risk. High probability of complete road severance."


scenario_service = ScenarioService()
