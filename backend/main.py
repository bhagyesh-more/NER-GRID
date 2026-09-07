"""NER-GRID FastAPI Application Entrypoint

Predictive Logistics & Accessibility Intelligence Network
SIH 2026 Problem Statement: SIH26002
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database.session import init_db, SessionLocal
from backend.database.models import DataSourceModel
from backend.api.router import root_router
from backend.api.v1.data_sources import INITIAL_SOURCES
from backend.services.gis.service import gis_service

# Logging Setup
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ner_grid")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and Shutdown lifecycle."""
    logger.info("Initializing NER-GRID database and tables...")
    init_db()

    # Pre-seed initial verified data sources and anchor locations
    db = SessionLocal()
    try:
        # Seed sources
        for s in INITIAL_SOURCES:
            existing = db.query(DataSourceModel).filter(DataSourceModel.code == s["code"]).first()
            if not existing:
                db.add(DataSourceModel(**s))
        db.commit()

        # Seed initial NER locations
        gis_service.seed_initial_ner_locations(db)
        logger.info("Database initialized successfully with verified NER seeds.")
    except Exception as e:
        logger.error(f"Error during startup data initialization: {e}")
        db.rollback()
    finally:
        db.close()

    yield
    logger.info("Shutting down NER-GRID application.")


app = FastAPI(
    title="NER-GRID Intelligence API",
    description=(
        "Mission-critical logistics and accessibility decision-support API "
        "for the North Eastern Region of India (SIH 2026 Problem SIH26002)."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware for modern frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(root_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )
