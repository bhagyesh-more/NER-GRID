"""Field Incident Reporting Endpoints"""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.database.models import IncidentReportModel
from backend.schemas.incident import IncidentReportCreate, IncidentReportResponse
from backend.schemas.common import DataOrigin

router = APIRouter(prefix="/incidents", tags=["Field Incidents"])


@router.get("", response_model=List[IncidentReportResponse])
def list_incidents(db: Session = Depends(get_db)):
    """Retrieve all active field reports submitted by operators and ground teams."""
    return db.query(IncidentReportModel).order_by(IncidentReportModel.reported_at.desc()).limit(50).all()


@router.post("", response_model=IncidentReportResponse)
def submit_incident_report(
    report: IncidentReportCreate,
    db: Session = Depends(get_db),
):
    """Submit a real-world field report. Strictly tagged with DataOrigin.REPORTED and unverified."""
    new_report = IncidentReportModel(
        location_name=report.location_name,
        report_type=report.report_type,
        description=report.description,
        latitude=report.latitude,
        longitude=report.longitude,
        provenance_status=DataOrigin.REPORTED.value,
        is_verified=False,
        reported_at=datetime.utcnow(),
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report
