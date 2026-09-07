"""Open Government Data (OGD) / data.gov.in Adapter

Manages access to Indian Open Government Data resources (MoRTH highway statistics,
IMD historical rainfall records, and PMGSY road connectivity).
"""
import logging
from typing import Any, Dict, List, Optional
import httpx
from backend.config import settings
from backend.schemas.common import DataOrigin
from backend.services.ingestion.base import BaseDataSource

logger = logging.getLogger(__name__)


class OGDAdapter(BaseDataSource):
    @property
    def name(self) -> str:
        return "data.gov.in (OGD India)"

    @property
    def code(self) -> str:
        return "ogd"

    @property
    def domain(self) -> str:
        return "government_statistics"

    @property
    def base_url(self) -> str:
        return settings.DATA_GOV_IN_BASE_URL

    @property
    def auth_type(self) -> str:
        return "api_key"

    @property
    def access_status(self) -> str:
        return "VERIFIED" if settings.DATA_GOV_IN_API_KEY else "PENDING_API_KEY"

    def get_registered_ner_catalogs(self) -> List[Dict[str, Any]]:
        """Known public datasets published on data.gov.in relevant to NER logistics."""
        return [
            {
                "resource_id": "9ef84268-d588-465a-a308-a864a43d0070",
                "title": "Sub-Division Wise Monthly Rainfall (1901-2015) - Assam & Meghalaya, Sub-Himalayan West Bengal & Sikkim",
                "publisher": "India Meteorological Department / MoES",
                "format": "CSV",
                "provenance_status": DataOrigin.OBSERVED.value,
                "url": "https://data.gov.in/resource/sub-division-wise-monthly-rainfall-1901-2015",
                "notes": "Authentic 100-year historical baseline for monsoonal intensity modeling.",
            },
            {
                "resource_id": "morth_nh_length_statewise",
                "title": "State-wise Length of National Highways in North Eastern Region",
                "publisher": "Ministry of Road Transport and Highways (MoRTH)",
                "format": "JSON / CSV",
                "provenance_status": DataOrigin.REPORTED.value,
                "url": "https://data.gov.in/resource/state-wise-length-national-highways-india",
                "notes": "Contains official gazetted lengths and route designations for NH-10, NH-06, NH-29.",
            },
        ]

    async def fetch_raw(self, resource_id: Optional[str] = None, **kwargs) -> Any:
        catalogs = self.get_registered_ner_catalogs()
        api_key = settings.DATA_GOV_IN_API_KEY

        if api_key and resource_id:
            # Query live OGD endpoint
            url = f"{self.base_url}/resource/{resource_id}"
            params = {"api-key": api_key, "format": "json", "limit": 10}
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        return {"live_data": resp.json(), "catalogs": catalogs}
            except Exception as e:
                logger.warning(f"Live OGD query failed: {e}")

        return {"catalogs": catalogs, "api_key_configured": bool(api_key)}

    def normalize(self, raw_data: Any) -> List[Dict[str, Any]]:
        return raw_data.get("catalogs", [])

    def validate_records(self, normalized_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [r for r in normalized_records if "resource_id" in r]
