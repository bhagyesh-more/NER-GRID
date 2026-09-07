"""Abstract Base Class for Data Source Adapters"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from backend.schemas.common import DataOrigin, IngestionStatus


class BaseDataSource(ABC):
    """Abstract base adapter enforcing the pipeline:

    FETCH RAW -> NORMALIZE -> VALIDATE -> INGEST
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name (e.g. 'OpenStreetMap', 'OSRM', 'India Meteorological Department')."""
        pass

    @property
    @abstractmethod
    def code(self) -> str:
        """Short identifier code (e.g. 'osm', 'osrm', 'imd', 'bhuvan', 'ogd')."""
        pass

    @property
    @abstractmethod
    def domain(self) -> str:
        """Data domain (e.g. 'road_network', 'routing', 'weather', 'hazard', 'elevation')."""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base endpoint or catalog URL."""
        pass

    @property
    def auth_type(self) -> str:
        return "none"

    @property
    def access_status(self) -> str:
        return "VERIFIED"

    @abstractmethod
    async def fetch_raw(self, **kwargs) -> Any:
        """Fetch raw payload from the upstream source."""
        pass

    @abstractmethod
    def normalize(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Transform raw source payload into standard NER-GRID canonical dictionaries."""
        pass

    @abstractmethod
    def validate_records(self, normalized_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter and validate physical and geographic bounds."""
        pass

    async def run_pipeline(self, **kwargs) -> Dict[str, Any]:
        """Execute complete ingestion pipeline with timing and error auditing."""
        started_at = datetime.utcnow()
        errors = []
        try:
            raw = await self.fetch_raw(**kwargs)
            normalized = self.normalize(raw)
            validated = self.validate_records(normalized)
            return {
                "status": IngestionStatus.SUCCESS,
                "source": self.name,
                "records_count": len(validated),
                "data": validated,
                "errors": errors,
                "started_at": started_at,
                "completed_at": datetime.utcnow(),
            }
        except Exception as exc:
            return {
                "status": IngestionStatus.FAILED,
                "source": self.name,
                "records_count": 0,
                "data": [],
                "errors": [str(exc)],
                "started_at": started_at,
                "completed_at": datetime.utcnow(),
            }
