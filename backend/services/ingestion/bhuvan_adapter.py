"""Bhuvan / ISRO / NRSC Geospatial Adapter

Manages access to Bhuvan OGC Web Map Services (WMS) and geospatial hazard layers.
Documents accessible vs restricted ISRO datasets without fabricating responses.
"""
import logging
from typing import Any, Dict, List, Optional
import httpx
from backend.config import settings
from backend.services.ingestion.base import BaseDataSource

logger = logging.getLogger(__name__)


class BhuvanAdapter(BaseDataSource):
    @property
    def name(self) -> str:
        return "Bhuvan / ISRO NRSC"

    @property
    def code(self) -> str:
        return "bhuvan"

    @property
    def domain(self) -> str:
        return "geospatial_hazard"

    @property
    def base_url(self) -> str:
        return settings.BHUVAN_WMS_BASE_URL

    @property
    def auth_type(self) -> str:
        return "bhuvan_session_token"

    @property
    def access_status(self) -> str:
        return "RESTRICTED_TOKEN"

    def get_known_ner_layers(self) -> List[Dict[str, Any]]:
        """Returns the catalog of known ISRO/Bhuvan thematic layers for the North East."""
        return [
            {
                "layer_name": "lulc:NER_50k_1516",
                "title": "Land Use Land Cover (1:50,000) North Eastern Region",
                "service_url": f"{self.base_url}?service=WMS&version=1.1.1&request=GetMap&layers=lulc:NER_50k_1516",
                "format": "image/png",
                "status": "ACCESSIBLE_WMS",
                "notes": "Available via Bhuvan standard OGC WMS with attribution to NRSC/ISRO.",
            },
            {
                "layer_name": "disaster:hazard_landslide_zones",
                "title": "ISRO Landslide Atlas of India Hazard Zonation",
                "service_url": "https://bhuvan-app1.nrsc.gov.in/disaster/disaster.php",
                "format": "vector_shapefile / PDF",
                "status": "OFFLINE_VERIFIED",
                "notes": "Publicly published in NRSC 2023 Landslide Atlas. Ingested as static vector dataset in NER-GRID.",
            },
            {
                "layer_name": "ndem:flood_inundation_assam",
                "title": "National Database for Emergency Management (NDEM) Real-Time Inundation",
                "service_url": "https://ndem.nrsc.gov.in",
                "format": "Restricted WMS",
                "status": "RESTRICTED_GOVERNMENT",
                "notes": "Requires NDMA/SDMA institutional login credentials. Documented for future phase integration.",
            },
        ]

    async def probe_wms_endpoint(self) -> Dict[str, Any]:
        """Probes the live Bhuvan endpoint and reports genuine status."""
        url = f"{self.base_url}?service=WMS&request=GetCapabilities"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                return {
                    "url": url,
                    "reachable": resp.status_code == 200,
                    "status_code": resp.status_code,
                    "response_bytes": len(resp.content),
                }
        except Exception as e:
            return {
                "url": url,
                "reachable": False,
                "error": str(e),
                "notes": "Bhuvan WMS endpoints frequently require departmental tokens or experience high latency. Catalog metadata is preserved.",
            }

    async def fetch_raw(self, **kwargs) -> Any:
        probe = await self.probe_wms_endpoint()
        layers = self.get_known_ner_layers()
        return {"probe": probe, "layers": layers}

    def normalize(self, raw_data: Any) -> List[Dict[str, Any]]:
        return raw_data.get("layers", [])

    def validate_records(self, normalized_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [r for r in normalized_records if "layer_name" in r]
