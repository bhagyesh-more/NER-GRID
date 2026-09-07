"""OSRM (Open Source Routing Machine) Adapter

Calculates real-world driving routes, distances, durations, and alternative paths
using public OSRM / self-hosted OSRM endpoints.
All route geometries and travel times are strictly tagged with DataOrigin.PREDICTED.
"""
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
import httpx
from backend.config import settings
from backend.schemas.common import DataOrigin
from backend.services.cache import cache_service
from backend.services.validation import GeospatialValidator, ValidationError
from backend.services.ingestion.base import BaseDataSource

logger = logging.getLogger(__name__)


class OSRMAdapter(BaseDataSource):
    @property
    def name(self) -> str:
        return "OSRM"

    @property
    def code(self) -> str:
        return "osrm"

    @property
    def domain(self) -> str:
        return "routing"

    @property
    def base_url(self) -> str:
        return settings.OSRM_BACKEND_URL

    async def calculate_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        origin_name: str = "Origin",
        dest_name: str = "Destination",
        alternatives: bool = True,
        waypoints: Optional[List[Tuple[float, float]]] = None,
    ) -> Dict[str, Any]:
        """Compute real route via OSRM driving service."""
        # 1. Validate coordinates
        GeospatialValidator.validate_coordinates(origin_lat, origin_lon)
        GeospatialValidator.validate_coordinates(dest_lat, dest_lon)

        # 2. Build coordinate string: lon,lat;[via_lon,via_lat;...]dest_lon,dest_lat
        coord_parts = [f"{origin_lon:.5f},{origin_lat:.5f}"]
        if waypoints:
            for wlat, wlon in waypoints:
                GeospatialValidator.validate_coordinates(wlat, wlon)
                coord_parts.append(f"{wlon:.5f},{wlat:.5f}")
        coord_parts.append(f"{dest_lon:.5f},{dest_lat:.5f}")
        coords_str = ";".join(coord_parts)

        # 3. Check Cache
        cache_key = f"osrm_route_{coords_str}_{alternatives}"
        cached = cache_service.get(cache_key)
        if cached:
            return cached

        # 4. Request from real OSRM service
        url = f"{self.base_url}/route/v1/driving/{coords_str}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "alternatives": "true" if alternatives else "false",
            "steps": "false",
        }
        headers = {"User-Agent": "NER-GRID-SIH2026/1.0 (sih2026-ner-grid@project.org)"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"OSRM returned HTTP {resp.status_code}: {resp.text}")
            raw_data = resp.json()

        if raw_data.get("code") != "Ok" or not raw_data.get("routes"):
            raise ValueError(f"OSRM pathfinding failed with status code: {raw_data.get('code')}")

        # 5. Normalize
        normalized = self._parse_osrm_response(
            raw_data=raw_data,
            origin_name=origin_name,
            dest_name=dest_name,
            origin_coords=(origin_lat, origin_lon),
            dest_coords=(dest_lat, dest_lon),
            source_url=str(resp.url),
        )

        # 6. Cache for 6 hours
        cache_service.set(cache_key, normalized, ttl_seconds=21600)
        return normalized

    def _parse_osrm_response(
        self,
        raw_data: Dict[str, Any],
        origin_name: str,
        dest_name: str,
        origin_coords: Tuple[float, float],
        dest_coords: Tuple[float, float],
        source_url: str,
    ) -> Dict[str, Any]:
        routes = raw_data.get("routes", [])
        primary = routes[0]
        primary_geometry = primary.get("geometry", {})

        # Compute alternative routes if returned
        alternatives = []
        for idx, alt in enumerate(routes[1:], start=1):
            alternatives.append({
                "route_index": idx,
                "distance_km": round(alt.get("distance", 0.0) / 1000.0, 2),
                "duration_minutes": round(alt.get("duration", 0.0) / 60.0, 1),
                "summary": f"Alternative route via {alt.get('legs', [{}])[0].get('summary', 'secondary corridor')}",
                "geometry": alt.get("geometry", {}),
            })

        return {
            "origin_name": origin_name,
            "destination_name": dest_name,
            "origin_lat": origin_coords[0],
            "origin_lon": origin_coords[1],
            "dest_lat": dest_coords[0],
            "dest_lon": dest_coords[1],
            "distance_km": round(primary.get("distance", 0.0) / 1000.0, 2),
            "duration_minutes": round(primary.get("duration", 0.0) / 60.0, 1),
            "geometry": primary_geometry,
            "alternatives": alternatives,
            "provider": self.name,
            "source_url": source_url,
            "provenance_status": DataOrigin.PREDICTED.value,
        }

    async def fetch_raw(self, **kwargs) -> Any:
        return await self.calculate_route(**kwargs)

    def normalize(self, raw_data: Any) -> List[Dict[str, Any]]:
        return [raw_data]

    def validate_records(self, normalized_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        valid = []
        for r in normalized_records:
            if r.get("distance_km", 0) > 0 and r.get("geometry", {}).get("coordinates"):
                valid.append(r)
        return valid
