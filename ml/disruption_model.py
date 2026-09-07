"""Explainable Baseline Disruption Model for NER-GRID

Calculates multi-hazard disruption probability (0-100%), risk levels,
contributing factors, confidence ratings, and mission suitability.
Designed with clear, physically explainable weights.
"""
import uuid
from typing import Dict, Any, List, Tuple
from backend.schemas.scenario import (
    RiskLevel,
    MissionSuitability,
    MissionType,
    ContributingFactor,
    RouteDisruptionAnalysis,
)


class DisruptionModel:
    def __init__(self):
        # Configurable explainable weights
        self.w_rain = 0.35
        self.w_antecedent = 0.25
        self.w_geology = 0.25
        self.w_topo = 0.15

    def calculate_disruption(
        self,
        features: Dict[str, Any],
        simulated_event_penalty: float = 0.0,
        simulated_event_description: str = "",
        mission_type: MissionType = MissionType.GENERAL_LOGISTICS,
        data_freshness_hours: float = 0.5,
    ) -> Dict[str, Any]:
        """Calculates disruption probability, risk level, confidence, and contributing factors."""
        factors: List[ContributingFactor] = []

        # 1. Rainfall Trigger Component (0 - 100)
        p_24h = features.get("precip_24h_mm", 0.0)
        ratio_24h = features.get("rainfall_24h_ratio", 0.0)
        # Scaled: ratio of 1.0 (meeting threshold) gives ~60 points; 1.5 gives 90 points
        rain_score = min(100.0, ratio_24h * 60.0)
        if rain_score > 15.0:
            factors.append(ContributingFactor(
                factor_name="Current / 24h Precipitation",
                impact_weight=round(self.w_rain * (rain_score / 100.0), 3),
                description=f"24h rainfall of {p_24h:.1f} mm ({ratio_24h * 100:.0f}% of district trigger threshold).",
                signal_type="meteorological",
            ))

        # 2. Antecedent Moisture Component (72h accumulation)
        p_72h = features.get("antecedent_72h_mm", 0.0)
        ratio_72h = features.get("rainfall_72h_ratio", 0.0)
        antecedent_score = min(100.0, ratio_72h * 55.0)
        if antecedent_score > 15.0:
            factors.append(ContributingFactor(
                factor_name="Antecedent Soil Moisture (72h)",
                impact_weight=round(self.w_antecedent * (antecedent_score / 100.0), 3),
                description=f"72h cumulative precipitation of {p_72h:.1f} mm elevated pore-water pressure.",
                signal_type="meteorological",
            ))

        # 3. Geological Hazard Baseline (NRSC Landslide Atlas)
        geo_risk = features.get("peak_geological_risk", 40.0)
        dominant_dist = features.get("dominant_district", "East Sikkim")
        geo_score = geo_risk  # NRSC risk is 0 - 100
        if geo_score > 30.0:
            factors.append(ContributingFactor(
                factor_name=f"NRSC Geological Susceptibility ({dominant_dist})",
                impact_weight=round(self.w_geology * (geo_score / 100.0), 3),
                description=f"Passes through {dominant_dist} classified as high landslide susceptibility in NRSC Atlas.",
                signal_type="geological",
            ))

        # 4. Topography & Mountain Gorge Exposure
        gorge_exp = features.get("gorge_exposure", 0.5)
        topo_score = gorge_exp * 100.0
        if topo_score > 30.0:
            factors.append(ContributingFactor(
                factor_name="Mountain Gorge Confinement",
                impact_weight=round(self.w_topo * (topo_score / 100.0), 3),
                description="Constrained mountain corridor alongside active river valley.",
                signal_type="infrastructure",
            ))

        # 5. Direct Event or Simulation Penalty
        event_score = simulated_event_penalty
        if event_score > 0.0:
            factors.append(ContributingFactor(
                factor_name="Simulated / Reported Disruption",
                impact_weight=round(min(1.0, event_score / 100.0), 3),
                description=simulated_event_description or "Direct road blockage or severe hazard event.",
                signal_type="simulated",
            ))

        # Multi-factor synthesis
        raw_prob = (
            (self.w_rain * rain_score) +
            (self.w_antecedent * antecedent_score) +
            (self.w_geology * geo_score) +
            (self.w_topo * topo_score) +
            event_score
        )
        disruption_probability = round(min(100.0, max(5.0, raw_prob)), 1)

        # Determine Risk Level
        if disruption_probability <= 25.0:
            risk_level = RiskLevel.LOW
        elif disruption_probability <= 50.0:
            risk_level = RiskLevel.MEDIUM
        elif disruption_probability <= 75.0:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL

        # Calculate Confidence Score (0 - 100%)
        # Factors: freshness, signal completeness, source verification
        freshness_penalty = min(35.0, data_freshness_hours * 1.5)
        signal_count = len(features.get("key_districts", []))
        signal_bonus = min(10.0, signal_count * 5.0)
        missing_penalty = 0.0 if signal_count > 0 else 15.0
        base_confidence = 85.0 - freshness_penalty + signal_bonus - missing_penalty
        confidence = round(min(98.0, max(25.0, base_confidence)), 1)

        # Determine Mission Suitability
        suitability = self._evaluate_mission_suitability(disruption_probability, mission_type)

        # Sort factors by impact weight descending
        factors.sort(key=lambda f: f.impact_weight, reverse=True)

        return {
            "disruption_probability": disruption_probability,
            "predicted_risk_score": disruption_probability,
            "predicted_risk_level": risk_level,
            "confidence": confidence,
            "contributing_factors": factors,
            "mission_suitability": suitability,
        }

    def _evaluate_mission_suitability(
        self,
        risk_score: float,
        mission_type: MissionType,
    ) -> MissionSuitability:
        if mission_type == MissionType.MEDICAL_EMERGENCY:
            # Low risk tolerance: cannot afford entrapment
            if risk_score > 65.0:
                return MissionSuitability.CRITICAL_AVOID
            elif risk_score > 35.0:
                return MissionSuitability.LOW
            elif risk_score > 20.0:
                return MissionSuitability.MEDIUM
            return MissionSuitability.HIGH

        elif mission_type == MissionType.HEAVY_FREIGHT:
            # High rollover/sinking hazard
            if risk_score > 70.0:
                return MissionSuitability.CRITICAL_AVOID
            elif risk_score > 45.0:
                return MissionSuitability.LOW
            elif risk_score > 25.0:
                return MissionSuitability.MEDIUM
            return MissionSuitability.HIGH

        elif mission_type == MissionType.RELIEF_CONVOY:
            # Higher resilience to moderate hazards
            if risk_score > 80.0:
                return MissionSuitability.CRITICAL_AVOID
            elif risk_score > 55.0:
                return MissionSuitability.LOW
            elif risk_score > 30.0:
                return MissionSuitability.MEDIUM
            return MissionSuitability.HIGH

        else:  # GENERAL_LOGISTICS
            if risk_score > 75.0:
                return MissionSuitability.CRITICAL_AVOID
            elif risk_score > 50.0:
                return MissionSuitability.LOW
            elif risk_score > 25.0:
                return MissionSuitability.MEDIUM
            return MissionSuitability.HIGH


disruption_model = DisruptionModel()
