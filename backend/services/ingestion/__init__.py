"""Ingestion Adapters for NER-GRID"""
from backend.services.ingestion.base import BaseDataSource
from backend.services.ingestion.osm_adapter import OSMAdapter
from backend.services.ingestion.osrm_adapter import OSRMAdapter
from backend.services.ingestion.imd_adapter import IMDAdapter
from backend.services.ingestion.bhuvan_adapter import BhuvanAdapter
from backend.services.ingestion.ogd_adapter import OGDAdapter

__all__ = [
    "BaseDataSource",
    "OSMAdapter",
    "OSRMAdapter",
    "IMDAdapter",
    "BhuvanAdapter",
    "OGDAdapter",
]
