"""Health Check Endpoint"""
from datetime import datetime
from fastapi import APIRouter
from backend.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "NER-GRID Backend",
        "problem_statement": "SIH26002",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "geographic_scope": "North Eastern Region (NER), India",
        "provenance_enforced": settings.ENFORCE_DATA_PROVENANCE,
    }
