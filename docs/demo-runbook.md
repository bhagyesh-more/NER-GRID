# NER-GRID — SIH 2026 Judge Demonstration Runbook (2–3 Minutes)
**Problem Statement SIH26002: Predictive Logistics & Accessibility Intelligence Network for North Eastern Region (NER)**

---

## Executive Summary & System Philosophy

NER-GRID is an AI-powered logistics decision-support platform engineered specifically for the complex, hazard-prone mountainous terrain of North East India (Sikkim, Assam, Meghalaya, Arunachal Pradesh, Nagaland, Manipur, Mizoram, Tripura).

### Ground Truth & Provenance Mandate (AGENTS.md Compliant)
Every data signal, route recommendation, and map overlay explicitly carries one of four non-negotiable provenance tags:
- **`OBSERVED`**: Authentic sensor readings (IMD Automatic Weather Stations, Open-Meteo API, OpenStreetMap road vectors, OSRM routing).
- **`REPORTED`**: Field incidents submitted by ground personnel or local emergency services, timestamped and preserved as unverified until corroboration.
- **`PREDICTED`**: Machine learning model inferences (Antecedent precipitation index, NRSC 2023 Landslide Atlas susceptibility, transit delay estimation).
- **`SIMULATED`**: Controlled what-if stress tests and simulated weather surges, strictly isolated from ground-truth database records.

---

## 2–3 Minute Live Demonstration Protocol

### Prerequisites
1. **Backend Server**: Active on `http://127.0.0.1:8000` (`python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`)
2. **Frontend Command Center**: Active on `http://localhost:5173` (`npm run dev` in `frontend/`)
3. **Database**: SQLite database initialized with verified NER coordinates at `data/ner_grid.db`.

---

### Step-by-Step Demonstration Script

#### 0:00 – 0:30: Introduction & Command Center Overview
1. **Open the Dashboard**: Navigate browser to `http://localhost:5173`.
2. **Explain the Interface**:
   - **Header**: Shows real-time backend health, active problem statement (`SIH26002`), and live provenance badge (`OBSERVED / PREDICTED`).
   - **Left Panel (Mission Control)**: Origin/destination selector, operational mission profiles (Medical Transit, Relief Convoy, Heavy Freight), and what-if simulation toggles.
   - **Center (Live GIS Map)**: Dark-themed vector map of North East India with terrain elevation context, state borders, and verified hospital locations.
   - **Right Panel (Route Intelligence)**: Real-time route candidate metrics, mission suitability scores, and explainability breakdown.
   - **Bottom Panel (Intelligence Feed)**: Live sensor inputs, data sources (IMD, NRSC ISRO, OSM), early warning bulletins, and before/after scenario comparison.

#### 0:30 – 0:55: Baseline Mission Analysis
3. **One-Click Demo Launch**:
   - Click the green banner: **`⚡ PRELOAD DEMO MISSION`** in the Mission Control panel.
   - *Corridor loaded*: **Siliguri (West Bengal Gateway)** to **STNM Hospital (Gangtok, Sikkim)**.
   - *Mission Type*: **Medical Transit (Priority 1)**.
   - *Baseline State*: **Real Data Baseline (Observed)**.
4. **Inspect Route Evaluation**:
   - Two real highway alternatives are calculated:
     - **Route A (NH-10 via Teesta Gorge & Rangpo)**: ~114 km, ~198 min transit time. Marked as `⚡ FASTEST ROUTE`.
     - **Route B (Alternative via Lava / Reshi / Rorathang)**: ~138 km, ~262 min transit time. Marked as `🛡️ LOWEST-RISK`.
   - Explain that NH-10 traverses the fragile Sevoke-Teesta mountain gorge (high NRSC landslide susceptibility index of 92.5/100).
   - Show the **"Why This Decision?"** panel explaining the operational trade-offs and contributing hazard signals.

#### 0:55 – 1:30: Scenario 1 — SIMULATED Heavy Rainfall
5. **Trigger Monsoon Surge**:
   - In the What-If Simulation section, select:
     **`2. SIMULATED Heavy Rainfall (+65mm Rain)`**.
   - Note the header badge instantly updates to **`SIMULATED`** (amber warning).
6. **Show Dynamic Recalculation**:
   - **Disruption Probability Increases**: The Teesta Gorge route's predicted risk score jumps from moderate to **HIGH / CRITICAL** (>65%).
   - **Transit Delay Added**: Saturated soils and mud debris add +35 to +60 minutes of expected travel time.
   - **Recommendation Flip**: NER-GRID automatically re-routes the Medical Emergency to **Route B**!
   - **Trade-Off Explanation**: The decision explanation updates in real-time:
     > *"Route B is STRONGLY RECOMMENDED: Lower predicted disruption risk (32% vs 78%), avoiding gorge entrapment. Trade-off: accepts +45 min travel time for mission reliability."*
   - Point out the **Before → After Delta** table in the bottom drawer.

#### 1:30 – 1:55: Scenario 2 — SIMULATED Road Disruption & Field Incident
7. **Trigger Point Disruption**:
   - Select **`3. SIMULATED Road Disruption (NH-10 Gorge Block)`**.
   - Watch the map update: the blocked corridor segment is highlighted, disruption probability reaches 95%+, and route suitability becomes `CRITICAL_AVOID`.
8. **Submit a Crowdsourced Field Report**:
   - Click **`SUBMIT FIELD DISRUPTION REPORT`**.
   - Form inputs:
     - *Location*: **Rangpo Border Checkpoint**
     - *Disruption Type*: **Active Landslide / Mudflow**
     - *Details*: *"Rockfall and debris blocking one lane north of Rangpo bridge; heavy vehicles stranded."*
   - Click **Submit Incident Report**.
   - Notice the purple marker appears on the GIS map, flagged with **`REPORTED [UNVERIFIED]`** provenance.
   - Explain to judges: NER-GRID stores field reports with exact timestamps and coordinates, factors them into route accessibility, but does not blindly treat them as verified ground truth until confirmed.

#### 1:55 – 2:20: Demo Reset to Real Data Baseline
9. **Reset to Baseline**:
   - Click the red **`RESET SCENARIO`** button in the What-If Simulation panel.
   - The system immediately returns to **Real Data Baseline (Observed)**.
   - Provenance status reverts to **`PREDICTED / OBSERVED`**.
   - Route recommendations and risk levels return to standard operational baselines.
   - Explain: *Database observations remain 100% pristine and unpolluted by simulated tests.*

---

## Technical Verification Matrix for Evaluators

| Step | Component | Verification Evidence |
| :--- | :--- | :--- |
| **Real Data Ingestion** | Open-Meteo & IMD Normals | Live API call in `backend/services/ingestion/imd_adapter.py` |
| **Geological Risk Fusion**| NRSC ISRO Landslide Atlas 2023 | District rankings loaded from `data/processed/hazard_baseline.json` |
| **Routing Engine** | OpenStreetMap / OSRM | Highway polyline geometries rendered via MapLibre GL |
| **Prediction Model** | ML Disruption Model | `ml/disruption_model.py` calculating probability & confidence |
| **Multi-Objective Pareto**| Mission Optimization | Weighted scoring balancing ETA vs risk vs vehicle clearance |
| **Data Provenance** | Strict Taxonomy | Explicit `OBSERVED`, `REPORTED`, `PREDICTED`, `SIMULATED` metadata |
| **Graceful Degradation** | Offline / Missing Data | Fallback to cached baselines with explicit confidence penalties |

---

## Exact Commands to Run Locally

### 1. Backend Server
```bash
# From repository root
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive API Docs: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/api/v1/health`

### 2. Frontend GIS Dashboard
```bash
cd frontend
npm run dev
```
- Command Center URL: `http://localhost:5173`

### 3. Automated Test Suite
```bash
# Run complete test suite (28 unit tests + 11 end-to-end integration tests)
pytest -v
```
