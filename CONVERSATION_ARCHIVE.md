# Crop Water Footprint (CWF) ML Project: Complete Conversation & Architectural Archive

**Date:** August 23, 2026  
**Project Location:** `c:\Users\gopav\Desktop\22_0826`  
**GitHub Repository:** `https://github.com/gnbreddy/AI-based-Crop-water-footprint-predictor.git`  
**Conversation ID:** `f8d2fce9-a297-4a1e-804b-d6a0056d8e41`

---

## 1. Project Overview & Objectives

This project implements an agro-hydrological Machine Learning infrastructure to predict and analyze the **Crop Water Footprint (CWF)** — partitioned into **Green Water Footprint (GWF)** (rainfall consumed) and **Blue Water Footprint (BWF)** (irrigation consumed) — across **36 continuous years (1990–2025, 52,592 records)** using multi-source meteorological observations from Google Earth Engine (GEE) and histogram-based Gradient Boosted Decision Trees (LightGBM).

---

## 2. Directory & Module Breakdown

```
22_0826/
├── .gitignore                # Security filter protecting credentials, keys, and caches
├── .dockerignore             # Optimizes Docker build contexts
├── .env.example              # Template for configuring GEE project ID & database credentials
├── README.md                 # Public GitHub project documentation and quickstart
├── WALKTHROUGH.md            # Detailed 36-year mathematical and visual report
├── docker-compose.yml        # Multi-container orchestration (PostgreSQL + FastAPI + Worker + React Nginx)
├── Dockerfile.api            # Production container for FastAPI & LightGBM Machine Learning engine
├── Dockerfile.worker         # Production container for Asynchronous Streaming & Batch Ingestion
├── Dockerfile.frontend       # Multi-stage container for React 18 + Vite + Nginx Reverse Proxy
├── config.py                 # Central configuration, locked-in parameters & physical constants
├── schemas.py                # Pydantic data schemas for all 4 physical pillars & validation
├── db_models.py              # SQLAlchemy ORM models, audit tables, and auto-seeding
├── normalization_engine.py   # Decoupled physics translation layer (VPD, SSI, Rs/Ra, gamma)
├── crop_repository.py        # Plug-and-play dynamic crop & soil database repository
├── universal_engine.py       # Universal, location-agnostic CWF engine for any coordinates on Earth
├── api_gateway.py            # Production FastAPI gateway with dependency injection & audit logging
├── streaming_pipeline.py     # High-throughput asynchronous streaming & bulk batch processor
├── worker_entrypoint.py      # Graceful consumer worker entrypoint for container execution
├── extractor.py              # GEE authentication, 6-hourly extraction & direct local / Drive export
├── compiler.py               # Ingestion of multi-decade CSVs, cleaning, interpolation, and lag/rolling creation
├── trainer.py                # 25-epoch cyclic expanding window validation, locked production model trainer
├── evaluator.py              # Statistical evaluator across all 26 individual years (2000–2025)
├── evaluate_1990s.py         # Ground-truth comparison and evaluation engine for 1990–1999 hindcasts
├── hindcast_predictor.py     # Blind historical CWF prediction engine for 1990–1999
├── calibrator.py             # FAO-56 / WFN Crop Water Footprint calculator and L-BFGS-B coefficient optimizer
├── visualizer.py             # Feature importance charts, learning curves, CWF partitioning plots, Folium maps
├── mock_data_generator.py    # Multi-decade (2000-2025) synthetic 6-hourly data generator for offline testing
├── test_pipeline.py          # Automated pytest test suite (7 passing test suites)
├── main.py                   # Unified CLI orchestrator with support for all execution modes
├── app.py                    # Flask server with universal prediction endpoints
├── requirements.txt          # Pinned project dependencies (FastAPI, Pydantic, SQLAlchemy, LightGBM, psycopg2)
├── .github/workflows/
│   └── ci.yml                # Automated GitHub Actions CI/CD test and build workflow
├── frontend/                 # Modern React 18 + Vite + Tailwind CSS + Leaflet Dashboard
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── nginx.conf            # High-performance Nginx reverse proxy configuration
│   ├── index.html
│   └── src/
│       ├── api/cwfApi.js
│       ├── components/
│       │   ├── Header.jsx
│       │   ├── SimulationForm.jsx
│       │   ├── CwfMetricsCard.jsx
│       │   ├── FootprintChart.jsx
│       │   ├── GeospatialMap.jsx
│       │   └── AuditTable.jsx
│       ├── App.jsx
│       ├── main.jsx
│       └── index.css
├── data/                     # Ingested, engineered, comparison, hindcast, and epoch datasets
│   ├── universal_agri.db     # SQLite/PostgreSQL database for dynamic crops, soils, and audit records
│   └── ...
└── outputs/                  # Exported models, visualizations, and maps
    ├── final_production_model.pkl
    └── ...
```

---

## 3. Environment Parity & Containerization Architecture

| Service | Technology | Port | Role |
| :--- | :--- | :---: | :--- |
| **`db`** | PostgreSQL 16 Alpine | `5432` | Enterprise relational database with persistent storage volume |
| **`api`** | FastAPI + Python 3.12-slim | `8000` | Universal prediction gateway, Pydantic validation, LightGBM ML inference |
| **`worker`** | Python 3.12-slim | — | Asynchronous background streaming consumer & bulk database transaction worker |
| **`frontend`** | React 18 + Vite + Nginx | `3000` (`:80`) | Interactive client dashboard with automated reverse proxy routing to `/api/` |

---

## 4. Verification Status
- **Backend Test Suite (`pytest`)**: 7/7 test suites passing 100%.
- **Frontend Production Build (`vite build`)**: Clean build with 2,481 modules transformed into production assets.
- **CI/CD Workflow (`.github/workflows/ci.yml`)**: Automated backend pytest + frontend compilation pipeline.
