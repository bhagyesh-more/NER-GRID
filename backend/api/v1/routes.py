"""Routing API Endpoints"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.database.models import RouteRecordModel
from backend.schemas.routing import RouteRequest, RouteResponse, RouteAlternative
from backend.services.routing.service import routing_service

router = APIRouter(prefix="/routes", tags=["Routing"])


def _format_route_response(record: RouteRecordModel) -> RouteResponse:
    geometry = json.loads(record.geometry_geojson) if record.geometry_geojson else {"type": "LineString", "coordinates": []}
    alternatives_raw = json.loads(record.alternatives_json) if record.alternatives_json else []
    alternatives = [
        RouteAlternative(
            route_index=alt.get("route_index", 1),
            distance_km=alt.get("distance_km", 0.0),
            duration_minutes=alt.get("duration_minutes", 0.0),
            summary=alt.get("summary"),
            geometry=alt.get("geometry", {"type": "LineString", "coordinates": []}),
        )
        for alt in alternatives_raw
    ]
    return RouteResponse(
        id=record.id,
        origin_name=record.origin_name,
        destination_name=record.destination_name,
        distance_km=record.distance_km,
        duration_minutes=record.duration_minutes,
        geometry=geometry,
        alternatives=alternatives,
        provider=record.provider,
        source_url=record.source_url,
        provenance_status=record.provenance_status,
        calculated_at=record.calculated_at,
    )


@router.post("", response_model=RouteResponse)
async def calculate_route(
    request: RouteRequest,
    db: Session = Depends(get_db),
):
    """Compute real-world driving route using OSRM with distance, duration, and GeoJSON geometry."""
    try:
        route_record = await routing_service.get_route(db, request)
        return _format_route_response(route_record)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Route calculation failed: {str(e)}")


@router.get("", response_model=List[RouteResponse])
def list_recent_routes(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Retrieve history of calculated routes stored in the database."""
    records = routing_service.get_recent_routes(db, limit=limit)
    return [_format_route_response(r) for r in records]
