# NER-GRID: Free Hosting Deployment Audit Report
**SIH 2026 Problem Statement: SIH26002**  
*Predictive Logistics & Accessibility Intelligence Network for North Eastern India*

---

## 1. Executive Summary & Compatibility Assessment

This audit evaluates the deployment readiness of the **NER-GRID** prototype for zero-cost free cloud hosting for the Smart India Hackathon 2026.

### Architectural Compatibility Summary

| Proposed Tier | Technology | Repository Status | Compatibility Rating | Key Findings |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend** | Next.js → Vercel | Vite + React 19 SPA | **NEEDS CHANGE (Vite on Vercel)** | The existing codebase is a Vite SPA, not Next.js. **Do NOT migrate to Next.js**; Vercel natively hosts Vite SPAs as static sites out of the box with zero code changes. |
| **Backend** | FastAPI → Render Free Web Service | FastAPI (Python 3.10+) | **READY / NEEDS CHANGE (Config)** | FastAPI app is 100% compatible with Render Free Web Service. Created `backend/requirements.txt`. Requires environment variable configuration. |
| **Database** | PostgreSQL + PostGIS → Supabase Free | SQLite / SQLAlchemy | **READY** | Database models use standard SQLAlchemy data types (`Float`, `Text` GeoJSON). Native PostGIS C-extensions are not required by application code. Seamless connection via `DATABASE_URL`. |
| **Routing** | OSRM | OSRM HTTP Adapter | **READY** | Configured to query public OSRM router (`https://router.project-osrm.org`). Requires no dedicated OSRM server hosting on free tiers. |
| **Maps** | MapLibre + OpenStreetMap | MapLibre GL JS | **READY** | Configured in `frontend/package.json` with open-access tile sources (OpenStreetMap / CARTO raster & vector basemaps). |

---

## 2. Checklist Items Audit Matrix (20/20)

| # | Checklist Item | Current Implementation | Status | Required Change | Recommended Deployment Configuration |
| :-: | :--- | :--- | :-: | :--- | :--- |
| **1** | **Frontend Framework, Package Manager, Build & Start Commands** | React 19 + Vite 8.0 SPA (`package.json`), `npm` package manager (`package-lock.json`). Build command: `npm run build` (`tsc -b && vite build`), output to `dist`. | **NEEDS CHANGE** | Update Vercel project configuration to target `frontend/` subdirectory. Output directory set to `dist`. No framework conversion needed. | **Vercel Static Site**: Root Directory: `frontend`, Build Command: `npm run build`, Output Directory: `dist`. |
| **2** | **Backend Framework, Python Version, Dependencies & Start Command** | FastAPI (Python 3.10+ / 3.11). Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`. | **NEEDS CHANGE** | Added missing `backend/requirements.txt` containing `fastapi`, `uvicorn`, `pydantic`, `sqlalchemy`, `psycopg2-binary`, etc. | **Render Free Web Service**: Root Directory: `/` or `backend`, Build Command: `pip install -r backend/requirements.txt`, Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`. |
| **3** | **Database Configuration** | Defaults to `sqlite:///./data/ner_grid.db` in `backend/config.py`. `session.py` handles PostgreSQL via `DATABASE_URL`. | **NEEDS CHANGE** | Supply PostgreSQL connection string in `DATABASE_URL` env variable on Render web service. | **Supabase Free PostgreSQL**: Set `DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres?sslmode=require` in Render settings. |
| **4** | **PostgreSQL / PostGIS Configuration** | Models in `backend/database/models.py` store geometries as GeoJSON strings in `Text` fields and lat/lon floats. | **READY** | None required. Works natively on standard PostgreSQL on Supabase without mandatory spatial extensions. | Standard Supabase PostgreSQL instance (PostGIS extension optional but enabled by default on Supabase). |
| **5** | **Localhost URLs Audit** | Hardcoded `http://localhost:8000` fallback in `frontend/src/api/client.ts` line 10 (`import.meta.env.VITE_API_URL`). External APIs in `backend/config.py` use HTTPS domain URLs. | **NEEDS CHANGE** | Set `VITE_API_URL` environment variable in Vercel to point to deployed Render backend service URL. | **Vercel Environment Variable**: `VITE_API_URL=https://<your-render-app>.onrender.com`. |
| **6** | **Environment Variables** | Managed via `pydantic-settings` in `backend/config.py` loading from `.env`. Template in `.env.example`. | **READY** | Inject required env variables into Render and Vercel dashboards. | Define `ENVIRONMENT=production`, `DEBUG=false`, `DATABASE_URL`, and `VITE_API_URL` in cloud dashboards. |
| **7** | **Secret Leakage Audit** | Checked entire codebase with `grep_search`. Zero hardcoded passwords, tokens, or API keys. `.gitignore` ignores `.env` & credentials. | **READY** | None required. | Pass API keys (such as optional `DATA_GOV_IN_API_KEY`) via host environment variables. |
| **8** | **CORS Configuration** | `CORSMiddleware` in `backend/main.py` configured with `allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]`. | **READY** | Optionally restrict `allow_origins` to Vercel domain in production, or keep `*` for hackathon convenience. | Default wildcard CORS in `main.py` is ready for cross-origin API calls from Vercel to Render. |
| **9** | **File-System Storage & Persistence** | Local SQLite DB (`data/ner_grid.db`) and file cache (`data/cached/`). Ephemeral disk on Render resets local disk on restart. | **NEEDS CHANGE** | DB persistence moves to Supabase PostgreSQL. File cache (`CacheService`) self-initializes directory on container start; ephemeral cache reset on reboot is acceptable. | Use Supabase PostgreSQL for persistent data. Ephemeral disk cache on Render functions safely. |
| **10** | **Background Workers & Scheduled Processes** | Asynchronous weather ingestion uses FastAPI `BackgroundTasks` in-process threadpool (`backend/api/v1/ingestion.py`). | **READY** | None required. No external Celery or Redis worker binaries needed. | Runs natively inside standard single Uvicorn web process on Render. |
| **11** | **WebSocket Requirements** | 0 WebSocket dependencies. 100% of frontend-backend communication uses HTTP REST endpoints (`fetch` JSON API). | **READY** | None required. | Standard HTTP REST over Render Free Web Service. |
| **12** | **External API Integrations** | Ingests Open-Meteo, public OSRM, Nominatim, Overpass, and metadata catalogs (IMD, Bhuvan, OGD). All have open endpoints. | **READY** | None required. Provenance taxonomy (`OBSERVED`, `REPORTED`, `PREDICTED`, `SIMULATED`) strictly maintained. | External public APIs are accessible directly over outbound HTTPS from Render. |
| **13** | **OSRM / Routing Configuration** | `OSRMAdapter` points to `https://router.project-osrm.org`. Calculates real-world polyline geometries and driving durations. | **READY** | None required. Uses public OSRM router endpoint. | `OSRM_BACKEND_URL=https://router.project-osrm.org` in `config.py`. |
| **14** | **IMD / Bhuvan / data.gov.in Integrations** | Integrations in `backend/services/ingestion/` use fallback calibration with Open-Meteo and baseline hazard data (`hazard_baseline.json`). | **READY** | None required. Strict AGENTS.md compliance: zero faked government responses. | Works seamlessly in production without requiring private credentials. |
| **15** | **ML Model Files & Requirements** | `ml/disruption_model.py` is a lightweight analytical model using weighted formula calculations and JSON hazard baselines. | **READY** | None required. No large binary weight files (`.pkl`, `.onnx`, `.pt`) to store or load. | Loads instantaneously in Python RAM (<5MB total memory consumption). |
| **16** | **GPU Requirements** | 100% CPU-based computation. No PyTorch / CUDA / GPU requirements. | **READY** | None required. | Operates cleanly within Render Free Web Service limit of 512 MB RAM and shared CPU. |
| **17** | **Docker Configuration** | No `Dockerfile` present in root or backend. | **READY / NEEDS CHANGE (Optional)** | Render builds FastAPI natively from Python runtime via `requirements.txt`. Adding a Dockerfile is optional. | Use Render native Python runtime environment. |
| **18** | **Existing Database Migrations** | Database tables are created dynamically via SQLAlchemy `Base.metadata.create_all()` during FastAPI startup lifespan (`backend/main.py`). | **READY** | None required for initial deployment. Automatically initializes all tables on Supabase PostgreSQL. | Automatic table creation on app startup (`init_db()`). |
| **19** | **Existing Seed / Sample Data** | `INITIAL_SOURCES` and `seed_initial_ner_locations()` automatically populate data catalog and 10 NER settlements on startup. | **READY** | None required. Data provenance metadata tags (`OBSERVED`, `REPORTED`, etc.) pre-loaded. | Automatically seeds database on first boot. |
| **20** | **Existing Test Suite** | 39 automated unit, integration, and e2e tests in `tests/`. All 39 tests passing cleanly with 0 failures. | **READY** | Run `pytest -v` in CI/CD before deployment. | Include `pytest` run in build or pre-deployment check. |

---

## 3. Detailed Component Analysis

### A. Frontend (Vite + React 19 SPA)
- **Current State**: Built with Vite 8.0, React 19, TypeScript, Tailwind CSS, and MapLibre GL JS (`package.json`).
- **Compatibility**: Highly compatible with Vercel Static Site hosting. The user specification suggested Next.js, but Vite SPA is fully supported on Vercel without code refactoring.
- **Key Requirement**: Set `VITE_API_URL` to the public Render backend URL during Vercel build phase.

### B. Backend (FastAPI Python Service)
- **Current State**: Engineered with FastAPI, Pydantic v2, and SQLAlchemy. Includes full CORS support (`CORSMiddleware`).
- **Dependencies**: Created `backend/requirements.txt` listing all necessary packages (`fastapi`, `uvicorn`, `pydantic-settings`, `sqlalchemy`, `httpx`, `psycopg2-binary`).
- **Compatibility**: Fully compatible with Render Free Web Service (512MB RAM, shared CPU).

### C. Database (Supabase PostgreSQL)
- **Current State**: Models use standard SQLAlchemy data types. Ephemeral local SQLite DB replaced by PostgreSQL database.
- **Compatibility**: 100% compatible. Connecting Supabase PostgreSQL string (`postgresql://...`) automatically executes table creation (`init_db()`) and seeds initial verified NER locations and data sources upon service startup.

### D. Routing & ML Engine
- **Current State**: Queries public OSRM API (`router.project-osrm.org`) for driving distance, duration, and GeoJSON polyline geometry. ML disruption model is a lightweight analytical risk-fusion engine (`ml/disruption_model.py`) loading district hazard baselines from `data/processed/hazard_baseline.json`.
- **Compatibility**: Requires zero GPU acceleration, zero large binary downloads, and zero paid routing API subscriptions.

---

## 4. Exact Files That Need Modification Before Deployment

Before triggering cloud deployment, the following files need minor configuration updates:

1. **`backend/requirements.txt`** *(Created)*
   - **Status**: Already created during this audit.
   - **Purpose**: Defines exact Python dependencies for Render build environment.

2. **`frontend/src/api/client.ts`** *(Optional modification if hardcoding fallback, but env var supported)*
   - **Line 10**: `const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';`
   - **Modification**: Code already supports `import.meta.env.VITE_API_URL`. Inject `VITE_API_URL` in Vercel settings. No source code edit needed.

3. **`vercel.json`** *(NEW - Recommended for root directory routing)*
   - **File Path**: `frontend/vercel.json` or root configuration.
   - **Purpose**: Tells Vercel how to route single-page application routes to `index.html`.

4. **`render.yaml`** *(NEW - Recommended optional declarative infrastructure file)*
   - **File Path**: `render.yaml` in repository root.
   - **Purpose**: Configures Render Web Service build & start commands automatically.

---

## 5. Verification & Test Confirmation

- **Unit & Integration Test Status**: Executed `pytest -v` on full suite.
- **Results**: **39 passed out of 39 tests** (100% pass rate).
- **Tested Modules**: OSRM routing adapter, Open-Meteo weather adapter, OSM vector parser, ML disruption model, scenario simulation engine, API endpoint handlers, and geospatial coordinate validators.
