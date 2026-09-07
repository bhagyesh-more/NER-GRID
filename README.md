# NER-GRID
### Predictive Logistics & Accessibility Intelligence Network for North Eastern India
**Problem Statement SIH26002 | Smart India Hackathon 2026**

---

## 📌 Problem Overview & Strategic Context

The North Eastern Region (NER) of India—connecting Arunachal Pradesh, Assam, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, and Tripura through the fragile 22-kilometer Siliguri Corridor ("Chicken's Neck")—faces chronic supply chain disruption caused by severe monsoons, cloudbursts, Brahmaputra/Barak basin flash flooding, and recurrent landslides on critical national lifelines such as **NH-10** (Siliguri–Gangtok), **NH-29** (Dimapur–Kohima), and **NH-06** (Shillong–Silchar).

**NER-GRID** is an AI-powered logistics decision-support platform engineered to:
- Fuse real-time weather observations, satellite earth observation baselines, 30m digital elevation models, and road network topology.
- Predict multi-hazard transportation disruptions (landslide susceptibility, flash flood inundation risk).
- Assess supply chain vulnerability, critical bridge bottlenecks, and isolated community risks.
- Optimize multi-criteria, risk-resilient routing for essential freight, disaster relief, and medical transit.
- Provide actionable mission control intelligence to state disaster authorities, civil supplies departments, and fleet operators.

---

## 🔄 Core Architectural Concept

```
Sense ──► Predict ──► Assess ──► Optimize ──► Respond
```

1. **Sense**: Ingest real-time and baseline data from verified sources (IMD, Copernicus 30m DEM, OpenStreetMap, NRSC Landslide Atlas, Bhuvan, NESAC).
2. **Predict**: Estimate road segment disruption probabilities ($P_{disrupt}$) by modeling rainfall intensity, terrain slope, and historical hazard susceptibility.
3. **Assess**: Quantify corridor severance risks, travel time delays, critical chokepoints, and isolated node vulnerability.
4. **Optimize**: Execute Pareto multi-objective pathfinding balancing travel duration, risk index, road grade, and surface type.
5. **Respond**: Deliver interactive GIS decision dashboards, divergence advisories, emergency staging suggestions, and low-bandwidth dispatch manifests.

---

## 🛡️ Ground Truth & Data Integrity Mandate

NER-GRID operates under strict engineering principles defined in [AGENTS.md](file:///d:/Projects/NER-GRID/AGENTS.md):
- **Real-Data-First**: Real, legally accessible government and open geospatial datasets are prioritized over synthetic fixtures.
- **Strict Provenance Tagging**: All data records carry explicit taxonomy: `OBSERVED`, `REPORTED`, `PREDICTED`, or `SIMULATED`.
- **Zero Fabrication**: External government APIs are never simulated or faked. Fallback data must be explicitly flagged.
- **Transparent Optimization**: Routing decisions and risk scores are physically explainable, never black-box guesses.

---

## 📂 Repository Structure

```
NER-GRID/
├── frontend/             # Modern React / Vite GIS Mission Control (MapLibre GL / Deck.gl)
├── backend/              # FastAPI Python backend (Ingestion, Graph Routing, Risk Scoring)
├── ml/                   # Hazard models (Landslide susceptibility, flood inundation models)
├── data/
│   ├── raw/              # Raw ingested datasets (DEM tiles, OSM extracts, OGD tables)
│   ├── processed/        # Standardized GeoJSONs, cleaned road graphs, hazard indices
│   ├── cached/           # Cached weather forecasts and API responses
│   └── simulated/        # Explicitly tagged synthetic scenarios for edge-case testing
├── scripts/              # Data acquisition, ETL, and corridor extraction tools
├── tests/                # Automated unit and integration tests (ingestion, schemas, routing)
├── docs/                 # Architectural Decision Records (ADRs) and design documentation
├── README.md             # Project overview and orientation
├── AGENTS.md             # Contributor and AI coding standards & ethics
├── prototype-spec.md     # Detailed functional specification & mathematical formulation
├── data-sources.md       # Comprehensive feasibility research of all government & GIS sources
└── .env.example          # Environment variable template
```

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)
- Git

### 2. Environment Configuration
Copy the template and configure local keys:
```bash
cp .env.example .env
```

### 3. Documentation Reference
- **Functional Requirements & Math**: See [prototype-spec.md](file:///d:/Projects/NER-GRID/prototype-spec.md)
- **Data Source Profiles & Feasibility**: See [data-sources.md](file:///d:/Projects/NER-GRID/data-sources.md)
- **Engineering Standards**: See [AGENTS.md](file:///d:/Projects/NER-GRID/AGENTS.md)