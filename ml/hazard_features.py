"""Feature Engineering for NER-GRID Disruption Modeling

Extracts physical and meteorological features from real data:
- NRSC Landslide Atlas (ISRO 2023) district vulnerability
- IMD / Open-Meteo 24h and 72h rainfall accumulations
- Topographical mountain exposure
- Historical monsoonal baseline deviation
"""
import os
import json
import logging
from typing import Dict, List, Tuple, Any, Optional
from shapely.geometry import Point, LineString

logger = logging.getLogger(__name__)

BASELINE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "hazard_baseline.json")


class HazardFeatureStore:
    def __init__(self):
        self._load_baseline_data()

    def _load_baseline_data(self):
        try:
            with open(BASELINE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.district_matrix = data.get("district_hazard_matrix", {})
                self.climatology = data.get("historical_monthly_rainfall_normals_mm", {})
        except Exception as e:
            logger.warning(f"Could not load hazard_baseline.json: {e}")
            self.district_matrix = {}
            self.climatology = {}

    def get_district_for_coords(self, lat: float, lon: float) -> str:
        """Approximates district based on coordinates in NER corridors."""
        # Sikkim Corridor (NH-10)
        if 27.2 <= lat <= 27.5 and 88.5 <= lon <= 88.75:
            return "East Sikkim"
        if 27.1 <= lat < 27.2 and 88.45 <= lon <= 88.65:
            return "Pakyong"
        if 26.6 <= lat < 27.1 and 88.2 <= lon <= 88.55:
            return "Darjeeling"

        # Meghalaya / Assam Corridor (NH-06)
        if 25.4 <= lat <= 25.8 and 91.7 <= lon <= 92.2:
            return "East Khasi Hills"
        if 24.6 <= lat <= 25.1 and 92.6 <= lon <= 93.1:
            return "Cachar"
        if 25.1 <= lat < 25.4 and 92.5 <= lon <= 93.3:
            return "Dima Hasao"
        if 26.0 <= lat <= 26.3 and 91.5 <= lon <= 92.0:
            return "Kamrup Metropolitan"

        # Nagaland Corridor (NH-29)
        if 25.5 <= lat <= 25.8 and 94.0 <= lon <= 94.3:
            return "Kohima"

        # Default fallback if outside specific mapped clusters
        return "East Sikkim" if lat > 27.0 else "Kamrup Metropolitan"

    def extract_route_features(
        self,
        route_coords: List[List[float]],
        weather_data: Dict[str, Any],
        rainfall_data: Dict[str, Any],
        historical_rainfall_72h_mm: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Extract multi-hazard features along the full route geometry."""
        # 1. Intersected Districts & Geological Susceptibility
        sampled_districts = set()
        step = max(1, len(route_coords) // 15)  # sample ~15 points along the path
        for i in range(0, len(route_coords), step):
            lon, lat = route_coords[i][0], route_coords[i][1]
            dist = self.get_district_for_coords(lat, lon)
            sampled_districts.add(dist)

        # Calculate max and mean geological susceptibility from NRSC Atlas
        geo_scores = []
        key_districts = list(sampled_districts)
        for dist in key_districts:
            info = self.district_matrix.get(dist, {})
            score = info.get("nrsc_risk_score", 40.0)
            geo_scores.append(score)

        peak_geological_risk = max(geo_scores) if geo_scores else 40.0
        avg_geological_risk = sum(geo_scores) / len(geo_scores) if geo_scores else 40.0

        # 2. Meteorological Triggers
        precip_24h = rainfall_data.get("rainfall_mm", 0.0)
        # If 72h antecedent rainfall not provided, approximate as 2.1x 24h reading (soil saturation proxy)
        antecedent_72h = historical_rainfall_72h_mm if historical_rainfall_72h_mm is not None else round(precip_24h * 2.1, 1)

        # Trend estimation: if past 24h rain is high and temperature is dropping
        wind_speed = weather_data.get("wind_speed_kmh", 0.0)
        temp_c = weather_data.get("temperature_c", 20.0)

        # 3. Mountain / Gorge Corridor Exposure
        # Corridors crossing East Sikkim, Pakyong, Darjeeling (NH-10) or Dima Hasao (NH-27/06) have high gorge exposure
        gorge_exposure = 1.0 if any(d in ["East Sikkim", "Pakyong", "Darjeeling", "Kohima"] for d in key_districts) else 0.4

        # 4. Threshold Exceedance
        # Caine threshold comparison for the dominant district
        dominant_district = key_districts[0] if key_districts else "East Sikkim"
        dist_meta = self.district_matrix.get(dominant_district, {})
        threshold_24h = dist_meta.get("trigger_24h_rainfall_mm", 50.0)
        threshold_72h = dist_meta.get("trigger_72h_rainfall_mm", 100.0)

        rainfall_24h_ratio = precip_24h / threshold_24h if threshold_24h > 0 else 0.0
        rainfall_72h_ratio = antecedent_72h / threshold_72h if threshold_72h > 0 else 0.0

        return {
            "key_districts": key_districts,
            "peak_geological_risk": peak_geological_risk,
            "avg_geological_risk": avg_geological_risk,
            "precip_24h_mm": precip_24h,
            "antecedent_72h_mm": antecedent_72h,
            "rainfall_24h_ratio": rainfall_24h_ratio,
            "rainfall_72h_ratio": rainfall_72h_ratio,
            "gorge_exposure": gorge_exposure,
            "wind_speed_kmh": wind_speed,
            "temperature_c": temp_c,
            "dominant_district": dominant_district,
        }


feature_store = HazardFeatureStore()
