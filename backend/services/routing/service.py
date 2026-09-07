"""Routing Service for NER-GRID

Coordinates OSRM real-world routing, alternatives calculation, and route history logging.
"""
import json
import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.database.models import RouteRecordModel
from backend.schemas.routing import RouteRequest, RouteResponse, RouteAlternative, Waypoint
from backend.schemas.common import DataOrigin
from backend.services.ingestion.osrm_adapter import OSRMAdapter
from backend.services.validation import GeospatialValidator

logger = logging.getLogger(__name__)


class RoutingService:
    def __init__(self, adapter: Optional[OSRMAdapter] = None):
        self.adapter = adapter or OSRMAdapter()

    async def get_route(
        self,
        db: Session,
        request: RouteRequest,
    ) -> RouteRecordModel:
        """Calculate real route via OSRM, save to database, and return."""
        origin_lat = request.origin.latitude
        origin_lon = request.origin.longitude
        dest_lat = request.destination.latitude
        dest_lon = request.destination.longitude

        origin_name = request.origin.name or f"Origin ({origin_lat:.3f}, {origin_lon:.3f})"
        dest_name = request.destination.name or f"Destination ({dest_lat:.3f}, {dest_lon:.3f})"

        waypoints_coords = [
            (w.latitude, w.longitude) for w in (request.waypoints or [])
        ]

        # Calculate via OSRM adapter
        route_data = await self.adapter.calculate_route(
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            dest_lat=dest_lat,
            dest_lon=dest_lon,
            origin_name=origin_name,
            dest_name=dest_name,
            alternatives=request.alternatives,
            waypoints=waypoints_coords,
        )

        # Persist to database
        route_record = RouteRecordModel(
            provider=route_data["provider"],
            source_url=route_data.get("source_url"),
            origin_name=origin_name,
            destination_name=dest_name,
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            dest_lat=dest_lat,
            dest_lon=dest_lon,
            distance_km=route_data["distance_km"],
            duration_minutes=route_data["duration_minutes"],
            geometry_geojson=json.dumps(route_data["geometry"]),
            alternatives_json=json.dumps(route_data.get("alternatives", [])),
            provenance_status=DataOrigin.PREDICTED.value,
        )
        db.add(route_record)
        db.commit()
        db.refresh(route_record)
        return route_record

    def get_recent_routes(self, db: Session, limit: int = 20) -> List[RouteRecordModel]:
        return db.query(RouteRecordModel).order_by(RouteRecordModel.calculated_at.desc()).limit(limit).all()


routing_service = RoutingService()
