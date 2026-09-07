# NER-GRID Data Sources & Feasibility Matrix
**Comprehensive Assessment of Government, Geospatial, and Meteorological Feeds**  
**SIH 2026 Problem SIH26002: Predictive Logistics & Accessibility Intelligence for North Eastern India**

---

## 1. Executive Summary & Sourcing Philosophy

NER-GRID adheres to a strict **Real-Data-First** engineering discipline. To construct a legally compliant, robust, and reproducible prototype for the North Eastern Region (NER), this document evaluates every candidate data provider across 7 essential data domains:

1. **Meteorology & Precipitation**: India Meteorological Department (IMD) + calibrated meteorological fallbacks
2. **Space-Based Earth Observation & Land Use**: Bhuvan / NRSC (ISRO)
3. **Transportation & Highway Topology**: OpenStreetMap (OSM)
4. **National Highway & Rural Connectivity Registry**: data.gov.in / OGD Platform India
5. **Regional Geoportal & Flood Early Warning**: NESAC / NeSDR (ISRO Umiam)
6. **Hazard Baselines & Landslide Vulnerability**: NRSC Disaster Services & Landslide Atlas of India
7. **Topography & Elevation Models**: Copernicus DEM GLO-30 / SRTM 30m

---

## 2. Detailed Data Source Feasibility Profiles

### Source 1: India Meteorological Department (IMD)
* **Dataset / Service Name**: IMD Real-Time AWS/ARG Observations, District Nowcast & 5-Day Numerical Weather Prediction (NWP).
* **Official URL**: [https://mausam.imd.gov.in](https://mausam.imd.gov.in) | [https://city.imd.gov.in](https://city.imd.gov.in) | [http://dsp.imdpune.gov.in](http://dsp.imdpune.gov.in) (Climate Data Services)
* **Data Type & Formats**: JSON endpoints (internal web services), NetCDF gridded rainfall (0.25° × 0.25°), CSV station reports, PDF bulletins.
* **Geographic Coverage**: Pan-India with specific stations across the 8 NER states operated by Regional Meteorological Centre (RMC) Guwahati, Gangtok, Shillong, Agartala, and Itanagar.
* **Update Frequency**: Automatic Weather Stations (AWS): 15–60 min; District Nowcasts: every 3 hours; NWP daily forecasts: 2× daily (08:30 & 17:30 IST).
* **API / Download Method**:
  - Web scraping / REST requests to public endpoints on `mausam.imd.gov.in/api/`.
  - Historical gridded climate archives accessible via IMD Pune Climate Portal.
  - Calibrated Real-time Open API: Open-Meteo provides an open-access JSON API serving ECMWF/GFS weather feeds cross-calibrated with IMD radar/station data over Indian coordinates.
* **Authentication Requirements**: Public web endpoints require no authentication. Official institutional bulk access via IMD Pune requires formal academic/government registration.
* **Usage Restrictions**: Government of India copyright (Ministry of Earth Sciences). Public bulletins may be consumed with explicit attribution to IMD.
* **Feasibility for SIH Prototype**: **HIGH**.
* **Recommended Integration Method**:
  - Implement `IMDWeatherProvider` adapter that queries IMD district weather bulletins for the target corridor.
  - Implement `OpenMeteoProvider` as a high-resolution coordinate-level fallback ($0.1^\circ$ grid) tagged with `DataOrigin.PREDICTED` and explicit metadata.

---

### Source 2: Bhuvan / NRSC (National Remote Sensing Centre, ISRO)
* **Dataset / Service Name**: Bhuvan Thematic Geospatial Services (LULC 1:50k, Geomorphology, Road & Rail Vectors, CartoDEM).
* **Official URL**: [https://bhuvan.nrsc.gov.in](https://bhuvan.nrsc.gov.in) | [https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms](https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms)
* **Data Type & Formats**: OGC WMS/WMTS (PNG/JPEG raster tiles), OGC WFS (GML/GeoJSON), GeoTIFF (CartoDEM tiles).
* **Geographic Coverage**: Pan-India including total coverage of the North Eastern Region.
* **Update Frequency**: Thematic maps updated every 1–5 years; CartoDEM is static high-resolution baseline.
* **API / Download Method**:
  - OGC Standard WMS `GetMap` requests for map layering in GIS clients.
  - Manual tile-by-tile download via Bhuvan Web Portal for CartoDEM 30m.
* **Authentication Requirements**: Open WMS basemaps require standard HTTP headers or free developer session token. CartoDEM tile downloads require a free registered Bhuvan user account.
* **Usage Restrictions**: Free for research, education, and non-commercial developmental use under ISRO Data Policy. Attribution to "ISRO/NRSC Bhuvan" is mandatory.
* **Feasibility for SIH Prototype**: **HIGH**.
* **Recommended Integration Method**:
  - Integrate Bhuvan thematic WMS layers directly as contextual raster tile layers in the frontend MapLibre GL viewer.
  - Store sample CartoDEM/LULC rasters in `data/raw/bhuvan/` for ground-truth validation.

---

### Source 3: OpenStreetMap (OSM)
* **Dataset / Service Name**: OpenStreetMap Road Network, Transport Infrastructure & Critical Facilities (Bridges, Culverts, Fuel Stations, Hospitals).
* **Official URL**: [https://www.openstreetmap.org](https://www.openstreetmap.org) | [https://overpass-api.de](https://overpass-api.de) | [https://download.geofabrik.de/asia/india.html](https://download.geofabrik.de/asia/india.html)
* **Data Type & Formats**: GeoJSON, OSM XML, Protocolbuffer Binary Format (`.osm.pbf`).
* **Geographic Coverage**: Comprehensive road network for all 8 North Eastern States (National Highways, State Highways, Major District Roads, village roads, river crossing nodes).
* **Update Frequency**: Real-time / minutely continuous community updates.
* **API / Download Method**:
  - Real-time bounding box extraction via Overpass API (REST POST queries in Overpass QL).
  - Bulk regional extracts from Geofabrik (`india-latest.osm.pbf` or sub-region).
* **Authentication Requirements**: None. Open public access.
* **Usage Restrictions**: Open Database License (ODbL) 1.0. Attribution required: "© OpenStreetMap contributors".
* **Feasibility for SIH Prototype**: **VERY HIGH (Essential Baseline)**.
* **Recommended Integration Method**:
  - Use Overpass API to query the road network for our target demonstration corridors (e.g. NH-10 Siliguri–Gangtok and NH-06 Guwahati–Shillong–Silchar).
  - Parse highways into a network graph (`NetworkX` / OSRM) with road grade, surface (`asphalt`, `unpaved`, `gravel`), and bridge attributes.

---

### Source 4: data.gov.in / Open Government Data (OGD) Platform India
* **Dataset / Service Name**: MoRTH National Highway Route Lengths, Bridges Census, and PMGSY Rural Connectivity Registry.
* **Official URL**: [https://data.gov.in](https://data.gov.in) | [https://api.data.gov.in](https://api.data.gov.in)
* **Data Type & Formats**: JSON REST APIs, CSV, XLS, GeoJSON.
* **Geographic Coverage**: National and state-level breakdowns for Assam, Arunachal Pradesh, Meghalaya, Manipur, Mizoram, Nagaland, Sikkim, and Tripura.
* **Update Frequency**: Monthly to annual depending on reporting department.
* **API / Download Method**: REST GET requests passing `api-key` parameter.
* **Authentication Requirements**: Free registration on `data.gov.in` to obtain a developer API key.
* **Usage Restrictions**: Government Open Data License - India (GODL-India). Permits non-commercial and commercial reuse with attribution.
* **Feasibility for SIH Prototype**: **HIGH**.
* **Recommended Integration Method**:
  - Implement `OGDDataProvider` to query MoRTH national highway schedules and bridge asset datasets for NER routes.
  - Cache extracted tables in `data/raw/ogd/`.

---

### Source 5: NESAC / NeSDR (North Eastern Space Applications Centre)
* **Dataset / Service Name**: North Eastern Spatial Data Repository (NeSDR), Flood Early Warning System (FLEWS), Landslide Early Warning System (LEWS).
* **Official URL**: [https://nesdr.gov.in](https://nesdr.gov.in) | [https://nesac.gov.in](https://nesac.gov.in) | [https://flews.nesac.gov.in](https://flews.nesac.gov.in)
* **Data Type & Formats**: OGC WMS/WFS, GeoTIFF, Shapefile, Flood hazard alert bulletins (PDF).
* **Geographic Coverage**: Specifically engineered for the 8 North Eastern States (Brahmaputra and Barak basins, Meghalaya plateau, Sikkim corridors).
* **Update Frequency**: Basemaps periodic; FLEWS produces daily alerts during active monsoon season (May to October).
* **API / Download Method**: NeSDR Geoportal viewer, OGC WMS endpoint queries, daily bulletin publications.
* **Authentication Requirements**: Public viewing open; programmatic raw API access and real-time early warning data feeds require government / institutional clearance from NESAC Director.
* **Usage Restrictions**: ISRO/DOS institutional data policy. Public map views permitted; automated redistribution of raw FLEWS feeds requires authorization.
* **Feasibility for SIH Prototype**: **MEDIUM (Mixed)**:
  - *Feasible*: Public WMS layers for regional land cover/geomorphology, and published static flood zonation maps.
  - *Restricted*: Real-time raw FLEWS REST API requires institutional credentials.
* **Recommended Integration Method**:
  - Integrate NESAC public WMS layers into the interactive map.
  - Encode published NESAC flood hazard zonation methodology and historical district flood frequencies into our risk engine.
  - Document live FLEWS programmatic API as an institutional upgrade path.

---

### Source 6: NRSC Disaster Services & Landslide Atlas of India
* **Dataset / Service Name**: NRSC Landslide Atlas of India (ISRO, 2023), Bhuvan Disaster Management Support Services (NDEM).
* **Official URL**: [https://www.nrsc.gov.in/Landslide_Atlas_of_India](https://www.nrsc.gov.in/Landslide_Atlas_of_India) | [https://bhuvan-app1.nrsc.gov.in/disaster/disaster.php](https://bhuvan-app1.nrsc.gov.in/disaster/disaster.php)
* **Data Type & Formats**: Vector shapefiles, tabular district vulnerability indices, GeoPDF hazard atlases.
* **Geographic Coverage**: 147 landslide-prone districts across 17 Indian states, with deep coverage of Sikkim (Ranked #1 in landslide density per unit area), Mizoram, Nagaland, Meghalaya, and Assam.
* **Update Frequency**: Comprehensive decadal baseline (atlas based on 1998–2022 historical event database); post-event rapid mapping during disasters.
* **API / Download Method**: Official ISRO web publication download, Bhuvan disaster portal maps.
* **Authentication Requirements**: Publicly downloadable for scientific and educational use. NDEM real-time disaster portal requires NDMA/SDMA authorized credentials.
* **Usage Restrictions**: Public domain with mandatory citation to ISRO/NRSC (2023).
* **Feasibility for SIH Prototype**: **VERY HIGH**.
* **Recommended Integration Method**:
  - Digitize and ingest the district landslide exposure, vulnerability index, and historical spatial point density from the 2023 NRSC Atlas into `data/processed/hazard_zones/nrsc_landslide_atlas.json`.
  - Use this real ground truth as the baseline weight matrix for highway corridor vulnerability.

---

### Source 7: Publicly Accessible Elevation / Terrain Datasets (Copernicus DEM GLO-30 & SRTM)
* **Dataset / Service Name**: Copernicus DEM GLO-30 (30m Global Digital Surface Model) / NASA SRTM 30m.
* **Official URL**: [https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model](https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model) | AWS Open Data: `s3://copernicus-dem-30m` | [https://opentopography.org](https://opentopography.org)
* **Data Type & Formats**: Cloud-Optimized GeoTIFF (COG), 16-bit signed integer raster (elevation in meters).
* **Geographic Coverage**: Seamless global coverage, excellent quality across the steep gorges, passes, and valleys of North Eastern India.
* **Update Frequency**: High-precision static baseline.
* **API / Download Method**: Direct HTTPS / AWS S3 range-requests without rate limits; raster sampling via Python `rasterio` / `GDAL`.
* **Authentication Requirements**: None on AWS Open Data.
* **Usage Restrictions**: Completely free and open for any use under Copernicus Sentinels Data Policy.
* **Feasibility for SIH Prototype**: **VERY HIGH (Gold Standard)**.
* **Recommended Integration Method**:
  - Ingest $1^\circ \times 1^\circ$ DEM GeoTIFF tiles covering the demonstration corridors into `data/raw/elevation/`.
  - Compute slope gradient, aspect, and road elevation profiles dynamically to penalize steep ascents and identify landslide-triggering slope angles (> 30°).

---

## 3. Comparative Summary & Integration Matrix

| Source | Domain | Real-Data Access | Auth Needed | License / Terms | Prototype Role |
|---|---|---|---|---|---|
| **OpenStreetMap** | Road Network & Bridges | Direct REST / PBF | None | ODbL 1.0 | **Primary Routing Graph** |
| **Copernicus GLO-30** | 30m Elevation & Slope | Direct S3 / HTTPS | None | Open Access | **Terrain & Slope Engine** |
| **NRSC Landslide Atlas** | Historical Landslide Risk | Vector / Tabular | None | ISRO Public Domain | **Static Vulnerability Matrix** |
| **IMD / Open-Meteo** | Weather & Precipitation | REST JSON API | None / Free Key | OGD-India / Open | **Dynamic Hazard Trigger** |
| **data.gov.in (OGD)** | Highway / Bridge Assets | REST API | Free API Key | GODL-India | **Infrastructure Metadata** |
| **Bhuvan (ISRO)** | Satellite & LULC Layers | OGC WMS | Public / Token | ISRO Terms of Use | **GIS Visual Context Layers** |
| **NESAC NeSDR** | Regional Flood Zonation | WMS / Published Data | Institutional (for live FLEWS) | DOS / NESAC Policy | **Flood Baseline & WMS** |

---

## 4. Ground Truth Integrity Protocol

1. When real data is pulled from any of the sources above, the response payload stored in memory or database MUST include:
   ```json
   {
     "source_agency": "IMD",
     "origin": "OBSERVED",
     "retrieval_timestamp": "2026-09-07T23:00:00Z",
     "station_id": "GUW_42410",
     "confidence": 0.95
   }
   ```
2. In unit tests or offline demonstrations where external network connections are disabled, pre-cached extracts from `data/cached/` must be used rather than generated pseudo-random values.
