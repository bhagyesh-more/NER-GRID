"""NER-GRID Predictive Disruption & What-If Scenario Demonstration

Demonstrates the operational transformation from:
'How risky is this route now?'
to:
'How might changing conditions affect this route, and what should the logistics operator do?'

Walks through:
1. Baseline Route Evaluation under Real Observations (Siliguri -> Gangtok NH-10).
2. Simulated Monsoonal Cloudburst / Landslide What-If Scenario.
3. Before/After Route Comparison & Early Warning Alerts.
4. Recommendation Pivot from Route A to Route B.
"""
import sys
import os
import asyncio
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.session import init_db, SessionLocal
from backend.schemas.routing import Waypoint
from backend.schemas.scenario import (
    ScenarioAnalysisRequest,
    ScenarioVariableInput,
    ScenarioType,
    MissionType,
)
from backend.services.scenario.service import scenario_service


async def run_scenario_demo():
    print("=" * 80)
    print("NER-GRID: Predictive Disruption & What-If Scenario Engine Demo")
    print("Problem Statement: SIH26002 | Smart India Hackathon 2026")
    print("=" * 80)

    init_db()
    db = SessionLocal()

    try:
        # STEP 1: Mission & Route Definition
        print("\n[STEP 1 & 2] Mission Defined: Medical Emergency Convoy")
        print("  Origin:      Siliguri (West Bengal gateway)")
        print("  Destination: Gangtok (Sikkim capital)")
        print("  Corridor:    NH-10 Himalayan Mountain Lifeline")
        print("  Mission:     medical_emergency (High sensitivity to road entrapment)")

        # STEP 2 & 3: Current Baseline Conditions Evaluation
        print("\n[STEP 3] Evaluating CURRENT Real Conditions (OpenStreetMap + OSRM + Live Weather)...")
        baseline_req = ScenarioAnalysisRequest(
            origin=Waypoint(name="Siliguri", latitude=26.7271, longitude=88.4354),
            destination=Waypoint(name="Gangtok", latitude=27.3389, longitude=88.6138),
            mission_type=MissionType.MEDICAL_EMERGENCY,
            scenario_variables=None,  # Real Baseline
        )
        base_resp = await scenario_service.analyze_scenario(db, baseline_req)

        print("\n  --- BASELINE ROUTE ANALYSIS (BEFORE) ---")
        for r in base_resp.baseline_route_analysis:
            print(f"  * {r.route_name}:")
            print(f"      Distance:       {r.distance_km} km")
            print(f"      Baseline ETA:   {r.baseline_duration_minutes} mins (~{round(r.baseline_duration_minutes/60, 2)} hrs)")
            print(f"      Risk Score:     {r.predicted_risk_score}% ({r.predicted_risk_level.value})")
            print(f"      Disruption P:   {r.disruption_probability}%")
            print(f"      Suitability:    {r.mission_suitability.value}")

        print(f"\n  >> Baseline Recommendation: {base_resp.recommended_route_id.upper()}")
        print(f"     Reason: {base_resp.recommendation_reason}")

        # STEP 4, 5, 6: Simulated Cloudburst & Landslide Event
        print("\n" + "-" * 80)
        print("[STEP 4 & 5] INITIATING WHAT-IF SCENARIO: Severe Monsoonal Deluge & Teesta Landslide")
        print("  Simulation Variables:")
        print("  - Scenario Type:               landslide_event + heavy rainfall")
        print("  - Simulated Rainfall Surge:    +65.0 mm (triggers severe pore-water pressure)")
        print("  - Affected Primary Corridor:   NH-10 (Sevoke-Teesta gorge active hill-slip)")
        print("  - Provenance Status:           SIMULATED (Zero DB records altered)")

        sim_req = ScenarioAnalysisRequest(
            origin=Waypoint(name="Siliguri", latitude=26.7271, longitude=88.4354),
            destination=Waypoint(name="Gangtok", latitude=27.3389, longitude=88.6138),
            mission_type=MissionType.MEDICAL_EMERGENCY,
            scenario_variables=ScenarioVariableInput(
                scenario_type=ScenarioType.LANDSLIDE_EVENT,
                rainfall_increase_mm=65.0,
                blocked_location_or_corridor="NH-10 (Sevoke-Teesta Gorge)",
                speed_reduction_pct=50.0,
            ),
        )
        sim_resp = await scenario_service.analyze_scenario(db, sim_req)

        # STEP 7 & 8: Scenario Evaluation & Recommendation Pivot
        print("\n  --- SCENARIO ROUTE ANALYSIS (AFTER) ---")
        for r in sim_resp.scenario_route_analysis:
            print(f"  * {r.route_name}:")
            print(f"      Distance:       {r.distance_km} km")
            print(f"      Degraded ETA:   {r.predicted_duration_minutes} mins (~{round(r.predicted_duration_minutes/60, 2)} hrs)")
            print(f"      Risk Score:     {r.predicted_risk_score}% ({r.predicted_risk_level.value})")
            print(f"      Disruption P:   {r.disruption_probability}%")
            print(f"      Suitability:    {r.mission_suitability.value}")
            print(f"      Impact Note:    {r.expected_impact}")

        # STEP 9: Contributing Factors
        print("\n[STEP 9] Main Contributing Risk Factors (Explainable AI Breakdown):")
        for factor in sim_resp.scenario_route_analysis[0].contributing_factors:
            print(f"    - [{factor.signal_type.upper()}] {factor.factor_name} (Weight: {factor.impact_weight}): {factor.description}")

        # Early Warnings
        if sim_resp.early_warnings:
            print(f"\n[EARLY WARNINGS GENERATED: {len(sim_resp.early_warnings)} ALERT(S)]")
            for alert in sim_resp.early_warnings:
                print(f"  [! ALERT] Level: {alert.severity} | Corridor: {alert.affected_route}")
                print(f"            Reason: {alert.reason}")
                print(f"            Action: {alert.recommended_action}")

        # STEP 10 & 11: Final Operational Decision
        print("\n[STEP 10 & 11] OPERATOR DECISION & ACTIONABLE INTELLIGENCE:")
        print(f"  {sim_resp.changed_risks_summary}")
        print(f"  {sim_resp.changed_eta_summary}")
        print(f"\n  >>> RE-EVALUATED RECOMMENDATION: {sim_resp.recommended_route_id.upper()} <<<")
        print(f"  EXPLANATION: {sim_resp.recommendation_reason}")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(run_scenario_demo())
