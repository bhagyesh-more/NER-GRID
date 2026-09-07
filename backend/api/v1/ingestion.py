"""Ingestion Status and Pipeline Trigger API Endpoints"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from backend.database.session import get_db, SessionLocal
from backend.database.models import IngestionRunModel, DataSourceModel
from backend.schemas.ingestion import IngestionRunResponse
from backend.schemas.common import IngestionStatus
from backend.services.weather.service import weather_service
from backend.services.gis.service import gis_service

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.get("/status", response_model=List[IngestionRunResponse])
def get_ingestion_status(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Retrieve history of data ingestion runs and health status."""
    return db.query(IngestionRunModel).order_by(IngestionRunModel.started_at.desc()).limit(limit).all()


async def _run_weather_ingestion(source_code: str):
    db = SessionLocal()
    run = IngestionRunModel(
        source_name=f"Ingestion Job: {source_code}",
        status=IngestionStatus.SUCCESS.value,
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        targets = [
            {"name": "Gangtok", "lat": 27.3389, "lon": 88.6138},
            {"name": "Guwahati", "lat": 26.1445, "lon": 91.7362},
            {"name": "Shillong", "lat": 25.5788, "lon": 91.8933},
            {"name": "Silchar", "lat": 24.8333, "lon": 92.7789},
        ]
        records = 0
        for t in targets:
            await weather_service.get_or_fetch_weather(db, t["name"], t["lat"], t["lon"])
            records += 2  # 1 weather + 1 rainfall observation

        run.status = IngestionStatus.SUCCESS.value
        run.records_ingested = records
        run.completed_at = datetime.utcnow()
        db.commit()
    except Exception as e:
        run.status = IngestionStatus.FAILED.value
        run.errors_count = 1
        run.error_log = str(e)
        run.completed_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


@router.post("/trigger", response_model=dict)
async def trigger_ingestion(
    source: str = Query("weather", description="Source to ingest: 'weather' or 'locations'"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """Trigger an on-demand real data ingestion pipeline."""
    if source == "locations":
        count = gis_service.seed_initial_ner_locations(db)
        return {"status": "completed", "source": "locations", "records_ingested": count}
    elif source == "weather":
        if background_tasks:
            background_tasks.add_task(_run_weather_ingestion, "weather")
            return {"status": "started", "source": "weather", "message": "Weather ingestion running in background."}
        else:
            await _run_weather_ingestion("weather")
            return {"status": "completed", "source": "weather", "message": "Weather ingestion completed."}
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported ingestion source: '{source}'")
