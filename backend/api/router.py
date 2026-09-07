"""Central API Router for NER-GRID"""
from fastapi import APIRouter
from backend.api.v1.health import router as health_router
from backend.api.v1.locations import router as locations_router
from backend.api.v1.weather import router as weather_router
from backend.api.v1.rainfall import router as rainfall_router
from backend.api.v1.routes import router as routes_router
from backend.api.v1.data_sources import router as data_sources_router
from backend.api.v1.ingestion import router as ingestion_router
from backend.api.v1.scenario import router as scenario_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(locations_router)
api_v1_router.include_router(weather_router)
api_v1_router.include_router(rainfall_router)
api_v1_router.include_router(routes_router)
api_v1_router.include_router(data_sources_router)
api_v1_router.include_router(ingestion_router)
api_v1_router.include_router(scenario_router)

root_router = APIRouter()
root_router.include_router(health_router)
root_router.include_router(api_v1_router)
