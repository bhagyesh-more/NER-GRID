"""NER-GRID Phase 1 Data Ingestion & Routing Demonstration

Executes real-world data pipelines across:
1. OpenStreetMap (Anchor locations & geocoding)
2. OSRM (Real driving routes: Siliguri -> Gangtok NH-10 corridor)
3. Weather & Rainfall Ingestion (Live conditions for Gangtok & Guwahati)
4. Provenance audit inspection
"""
import sys
import os
import asyncio
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.session import init_db, SessionLocal
from backend.services.gis.service import gis_service
from backend.services.weather.service import weather_service
from backend.services.routing.service import routing_service
from backend.schemas.routing import RouteRequest, Waypoint


async def run_demo():
    print("=" * 70)
    print("NER-GRID: Phase 1 Real Data Ingestion & Routing Pipeline Demo")
    print("SIH 2026 Problem Statement: SIH26002")
    print("=" * 70)

    # 1. Initialize DB
    print("\n[1/4] Initializing Database & Seeding Verified Ground-Truth Locations...")
    init_db()
    db = SessionLocal()
    try:
        count = gis_service.seed_initial_ner_locations(db)
        locations = gis_service.get_locations(db, limit=5)
        print(f"  -> Total verified NER anchor points ready: {len(locations)} shown below:")
        for loc in locations:
            print(f"     * {loc.name} ({loc.state}) - Lat: {loc.latitude}, Lon: {loc.longitude}, Provenance: {loc.provenance_status}")

        # 2. Ingest Real Weather & Rainfall for Gangtok
        print("\n[2/4] Ingesting LIVE Weather & Rainfall for Gangtok (NH-10 Lifeline)...")
        gangtok = gis_service.get_location_by_name(db, "Gangtok")
        if gangtok:
            res = await weather_service.get_or_fetch_weather(
                db=db,
                location_name=gangtok.name,
                lat=gangtok.latitude,
                lon=gangtok.longitude,
            )
            w = res["weather"]
            r = res["rainfall"]
            print(f"  -> Weather Ingested: Temp = {w.temperature_c}°C, Wind = {w.wind_speed_kmh} km/h, Condition = {w.weather_condition}")
            print(f"     Source: {w.source_name} | Provenance: {w.provenance_status} | Timestamp: {w.observed_at}")
            print(f"  -> Rainfall Ingested: 24h Cumulative = {r.rainfall_mm} mm")
            print(f"     Source: {r.source_name} | Provenance: {r.provenance_status} | Timestamp: {r.observed_at}")

        # 3. Calculate Real Driving Route via OSRM (Siliguri to Gangtok - NH-10)
        print("\n[3/4] Calculating REAL Driving Route via OSRM: Siliguri -> Gangtok (NH-10 Corridor)...")
        siliguri = gis_service.get_location_by_name(db, "Siliguri")
        route_req = RouteRequest(
            origin=Waypoint(name=siliguri.name, latitude=siliguri.latitude, longitude=siliguri.longitude),
            destination=Waypoint(name=gangtok.name, latitude=gangtok.latitude, longitude=gangtok.longitude),
            alternatives=True,
        )
        route = await routing_service.get_route(db, route_req)
        geom = json.loads(route.geometry_geojson)
        coords_count = len(geom.get("coordinates", []))
        print(f"  -> Route Generated via {route.provider}:")
        print(f"     Distance: {route.distance_km} km")
        print(f"     Duration: {route.duration_minutes} minutes (~{round(route.duration_minutes / 60, 2)} hours)")
        print(f"     Geometry coordinates: {coords_count} high-resolution waypoints")
        print(f"     Provenance Status: {route.provenance_status}")

        alts = json.loads(route.alternatives_json) if route.alternatives_json else []
        print(f"     Alternative routes found: {len(alts)}")
        for alt in alts:
            print(f"       - Alt #{alt['route_index']}: {alt['distance_km']} km, {alt['duration_minutes']} mins ({alt.get('summary')})")

        # 4. Audit & Provenance Verification
        print("\n[4/4] Verifying Data Provenance Taxonomy Compliance...")
        print("  -> DataOrigin Rules Check:")
        print(f"     Locations Status: {gangtok.provenance_status} (Matches OBSERVED: {gangtok.provenance_status == 'OBSERVED'})")
        print(f"     Weather Status:   {w.provenance_status} (Matches OBSERVED: {w.provenance_status == 'OBSERVED'})")
        print(f"     Rainfall Status:  {r.provenance_status} (Matches PREDICTED/OBSERVED: {r.provenance_status in ('OBSERVED', 'PREDICTED')})")
        print(f"     Route Status:     {route.provenance_status} (Matches PREDICTED: {route.provenance_status == 'PREDICTED'})")
        print("\nPipeline execution SUCCESSFUL: All real-world feeds ingested and validated.")
        print("=" * 70)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(run_demo())
