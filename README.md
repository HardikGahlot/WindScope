# WindScope — UK Wind Forecast Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Tests-34%20Passing-brightgreen.svg)]()

WindScope is a production-minded energy analytics platform built for UK electricity utilities and wholesale power buyers. It retrospectively evaluates the wind generation forecasts available at day-ahead decision times against actual outturns recorded on the Great Britain transmission grid by Elexon BMRS.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Business Problem & Solution](#2-business-problem--solution)
3. [Key Features](#3-key-features)
4. [Architecture Diagram](#4-architecture-diagram)
5. [Technology Stack](#5-technology-stack)
6. [Data Sources & Official Documentation](#6-data-sources--official-documentation)
7. [Data Retrieval & Forecast Selection Methodology](#7-data-retrieval--forecast-selection-methodology)
8. [Decision-Date and Delivery-Date Interpretation](#8-decision-date-and-delivery-date-interpretation)
9. [Configurable Cutoff Assumption](#9-configurable-cutoff-assumption)
10. [Accuracy Metric Formulas](#10-accuracy-metric-formulas)
11. [Missing-Data Policy](#11-missing-data-policy)
12. [Data & Domain Limitations](#12-data--domain-limitations)
13. [Project Directory Structure](#13-project-directory-structure)
14. [Prerequisites](#14-prerequisites)
15. [Local Setup Instructions](#15-local-setup-instructions)
16. [Environment Variables](#16-environment-variables)
17. [Docker Instructions](#17-docker-instructions)
18. [Automated Tests & Actual Results](#18-automated-tests--actual-results)
19. [Public Frontend URL](#19-public-frontend-url)
20. [Public Backend & API Documentation URL](#20-public-backend--api-documentation-url)
21. [Deployment Instructions](#21-deployment-instructions)
22. [Security & Operational Considerations](#22-security--operational-considerations)
23. [AI Tools Disclosures](#23-ai-tools-disclosures)

---

## 1. Project Overview

UK electricity procurement requires trading desks to purchase wholesale electricity 24 hours prior to delivery. Wind power is weather-dependent and volatile. When entering day-ahead auctions (e.g., EPEX or Nord Pool auctions around 11:00 or internal desk deadlines at 09:30), traders must rely on National Grid ESO wind forecasts that have **already been published**.

**WindScope** reconstructs the exact forecast knowledge available at the decision cutoff, matches it against physical delivery settlement periods, and provides defensible accuracy benchmarks (MAE, RMSE, Forecast Bias, and MAPE) across January 2026.

---

## 2. Business Problem & Solution

### The Problem
- **Lookahead Bias in Naive Systems**: Standard dashboards frequently query "latest available forecast." If a forecast was published at 16:00 on the decision day, a trader at 09:30 could not have known it. Evaluating accuracy with post-cutoff forecasts produces invalid, overly optimistic metrics.
- **Resolution Mismatch**: Transmission operators publish wind forecasts (`WINDFOR`) at hourly intervals, whereas UK settlement periods (`FUELHH`) occur half-hourly (48 periods/day). Naive tools invent numbers or substitute zeros.
- **Distorted Percentage Metrics**: When wind generation is zero (calm night/curtailment), naive MAPE formulas divide by zero, crashing calculations or skewing figures.

### The Solution
- **Strict Retrospective Enforcement**: An inclusive cutoff boundary filter (`publishTime <= cutoff_utc`) guarantees zero lookahead bias.
- **Resolution Transparency**: Transparent gaps and visual flags in exact matching mode, with an optional block-hour mapping mode for commercial portfolio teams.
- **Statistically Defensible Analytics**: Rigorous MAE, RMSE, signed bias, and zero-actual-excluded MAPE with explicit exclusion tracking.

---

## 3. Key Features

- **Executive Overview Dashboard**: High-level KPIs showing Expected vs Actual MW, MAE, RMSE, Mean Bias, Observational Coverage, and the exact timestamp of the latest eligible publication.
- **Decision-Time Forecast Explorer**: Select any day in January 2026, customize the Europe/London decision cutoff time, and audit the candidate forecasts considered.
- **Interactive Time-Series Chart**: Built with Recharts, displaying half-hourly decision forecasts vs actuals with interactive tooltips and non-interpolated visual gaps.
- **January 2026 Daily Trends**: 31-day interactive chart of daily MAE and Bias with one-click date switching.
- **Settlement Records Audit Table**: Searchable, sortable, filterable audit ledger with data quality badges (`Hourly WINDFOR gap`, `Mapped from Hour`, `Deduped`).
- **CSV Data Export**: One-click download of reproducible, escaped CSV datasets containing delivery periods, timestamps, errors, cutoff context, and quality flags.
- **Interactive Methodology Modal**: Comprehensive in-app guide explaining Elexon endpoints, mathematical definitions, error sign conventions, and disclaimers.

---

## 4. Architecture Diagram

```mermaid
flowchart TD
    subgraph Upstream["Upstream National Market Operator"]
        BMRS_Actuals["Elexon BMRS /datasets/FUELHH/stream (Actuals)"]
        BMRS_Forecasts["Elexon BMRS /datasets/WINDFOR/stream (Forecasts)"]
    end

    subgraph Backend["Python 3.11 FastAPI Backend"]
        Client["ElexonClient (httpx, retries, rate-limit backoff)"]
        Cache[("SQLite Cache: data/cache/bmrs_cache.db")]
        DTUtils["DateTimeUtils (Europe/London & UTC)"]
        Selection["ForecastSelection Engine (Cutoff Filter & Versioning)"]
        Metrics["AccuracyMetrics Engine (MAE, RMSE, Bias, MAPE)"]
        Service["AnalysisService (Orchestrator & CSV Generator)"]
        Router["FastAPI REST Endpoints (/api/analysis/*)"]

        Client <-->|Cache or Fetch| Cache
        Client -->|Raw Records| Selection
        DTUtils --> Selection
        Selection --> Metrics
        Metrics --> Service
        Service --> Router
    end

    subgraph Frontend["React 18 + TypeScript + Tailwind CSS"]
        Shell["AppShell & TopBar"]
        Controls["DecisionControls (Date, Cutoff, Mode)"]
        Overview["ExecutiveOverview Cards"]
        Chart["ForecastActualChart (Recharts Time Series)"]
        TrendsChart["DailyAccuracyChart (31-Day Trend)"]
        Table["RecordsTable & CSV Downloader"]
        Modal["Methodology & Audit Modal"]

        Router <-->|Typed REST JSON / CSV| Frontend
    end

    Upstream --> Client
```

---

## 5. Technology Stack

### Backend
- **Python 3.11**
- **FastAPI 0.110+**: High-performance asynchronous API framework.
- **Pydantic v2**: Strict schema validation and typed responses.
- **httpx**: Asynchronous HTTP client with bounded retries and exponential backoff.
- **SQLite 3**: Standard-library persistent indexed storage for zero-dependency local caching.
- **pytest, pytest-asyncio, respx**: Automated testing and mock HTTP client boundaries.

### Frontend
- **React 18 & TypeScript (Strict Mode)**
- **Vite 5**: Fast development server and optimized build bundler.
- **Tailwind CSS 3.4**: Dark enterprise theme (`#0b1120`, navy slate, cyan, emerald accents).
- **Recharts 2.12**: Accessible, responsive time-series and bar chart visualizations.
- **Lucide React**: Clean enterprise iconography.
- **Vitest & Testing Library**: Component unit tests and user interaction verification.

### DevOps & Containerization
- **Docker & Docker Compose**: Multi-stage builds and isolated container environments.
- **Nginx Alpine**: Static SPA serving and reverse-proxying.

---

## 6. Data Sources & Official Documentation

| Dataset | Endpoint Path | Fields of Interest | Purpose |
| :--- | :--- | :--- | :--- |
| **FUELHH** | `/datasets/FUELHH/stream` | `startTime`, `generation`, `fuelType`, `settlementDate`, `settlementPeriod` | Actual outturn generation by fuel type. Filtered strictly for `fuelType == 'WIND'`. |
| **WINDFOR** | `/datasets/WINDFOR/stream` | `startTime`, `publishTime`, `generation` | Historical wind generation forecast runs published by NGESO. |

- **Official BMRS Portal**: [https://bmrs.elexon.co.uk/api-documentation](https://bmrs.elexon.co.uk/api-documentation)
- **Base API Host**: `https://data.elexon.co.uk/bmrs/api/v1`
- **Swagger JSON Specification**: `https://data.elexon.co.uk/swagger/v1/swagger.json`

### Verified Historical Ingestion Scope
- **FUELHH Actuals**: Exactly **1,584 records** spanning 33 calendar days (`2026-01-01` to `2026-02-02`, $33 \times 48 = 1,584$). This completely covers all 31 delivery days for January 2026 decisions (`2026-01-02` through `2026-02-01`), plus the `2026-02-02` buffer. Zero null or missing actual records exist in this window.
- **WINDFOR Forecasts**: Exactly **18,688 records** published between `2025-12-31T02:30:00Z` and `2026-01-31T22:30:00Z` across 256 publication runs, covering delivery start times through `2026-02-02T21:00:00Z`.
- **Units**: All values represent national Great Britain average wind generation in **Megawatts (MW)**.

---

## 7. Data Retrieval & Forecast Selection Methodology

To eliminate lookahead bias:
1. **Cutoff Construction**: For a selected decision date $D$ and cutoff string (e.g. `09:30`), the cutoff is localized to `Europe/London` and converted to UTC: `cutoff_utc`.
2. **Candidate Retrieval**: WINDFOR records targeting delivery date $D+1$ are queried across publications.
3. **Inclusive Cutoff Filter**: A forecast is eligible if and only if $\text{publishTime} \le \text{cutoff\_utc}$. Forecasts published strictly after the cutoff are discarded and counted as excluded.
4. **Latest Eligible Selection**: Among eligible candidates for a delivery period, the record with the maximum $\text{publishTime}$ is selected.
5. **Provenance Tracking**: Candidate counts, exclusion counts, and the chosen publication timestamp are stored alongside the record.

---

## 8. Decision-Date and Delivery-Date Interpretation

In UK wholesale power procurement:
- **Decision Date ($D$)**: 1 January 2026 through 31 January 2026. The calendar day on which commercial purchasing decisions are finalized.
- **Delivery Date ($D+1$)**: The following day, 2 January 2026 through 1 February 2026. The calendar day during which the physical electricity is generated and fed into the grid.

---

## 9. Configurable Cutoff Assumption

The application defaults to **09:30 Europe/London** as an initial demonstration assumption for day-ahead purchasing decisions. This is clearly labeled as an operational assumption rather than a universal statutory deadline.
Users can modify this cutoff dynamically in the UI (e.g., to `11:00` for day-ahead auctions or `12:00` for midday gate closure). The selection engine dynamically re-evaluates candidate eligibility in real time.

---

## 10. Accuracy Metric Formulas

Let $F$ = forecast generation in MW, $A$ = actual generation in MW, and $e = F - A$ across $N$ valid matched pairs:

- **Error Sign Convention**:
  - $e > 0$: **Overforecast** (forecast overestimated actual output).
  - $e < 0$: **Underforecast** (forecast underestimated actual output).
- **Mean Absolute Error (MAE)**:
  $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |F_i - A_i|$$
- **Root Mean Squared Error (RMSE)**:
  $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (F_i - A_i)^2}$$
- **Mean Forecast Bias**:
  $$\text{Bias} = \frac{1}{N} \sum_{i=1}^N (F_i - A_i)$$
- **Mean Absolute Percentage Error (MAPE)**:
  $$\text{MAPE} = \frac{1}{M} \sum_{j=1}^M \left|\frac{F_j - A_j}{A_j}\right| \times 100 \quad (A_j \neq 0)$$
  *Zero actual values ($A_j = 0$) are strictly excluded to prevent division by zero, and the exclusion count is reported.*

---

## 11. Missing-Data Policy

- **No Silent Zero Replacement**: Missing forecasts or actuals are never treated as zero.
- **No Interpolation Artifacts**: Charts use `connectNulls={false}` to show clean visual gaps.
- **Transparent Quality Flags**: Unmatched half-hours are explicitly flagged as `HOURLY_RESOLUTION_NO_EXACT_HALF_HOUR_FORECAST`.
- **Unavailable Status**: When $N = 0$, metrics return `null` with status `no_matched_pairs`.

---

## 12. Data & Domain Limitations

1. **Procurement Scope Limitation**: Wind forecast errors alone do not dictate the net volume of power a utility must purchase. Consumer demand, solar generation, interconnector flows, and plant outages are outside the national wind scope.
2. **Financial Savings**: WindScope evaluates physical and statistical accuracy and does not calculate financial trading profits or monetary savings.
3. **Hourly vs Half-Hourly Granularity**: NGESO issues WINDFOR forecasts at hourly intervals, whereas UK settlement periods are half-hourly.

---

## 13. Project Directory Structure

```text
first_project/
├── backend/
│   ├── app/
│   │   ├── api/routes.py            # FastAPI REST routes (/health, /overview, /export, etc.)
│   │   ├── config.py                # Environment configuration and CORS settings
│   │   ├── main.py                  # App entry point, CORS, and error handlers
│   │   ├── models/schemas.py        # Pydantic v2 data models and responses
│   │   ├── services/
│   │   │   ├── accuracy_metrics.py  # MAE, RMSE, Bias, and MAPE computation
│   │   │   ├── analysis_service.py  # Orchestration, multi-day trends, and CSV export
│   │   │   ├── cache_service.py     # SQLite persistent storage (bmrs_cache.db)
│   │   │   ├── elexon_client.py     # Resilient HTTP client for FUELHH & WINDFOR
│   │   │   └── forecast_selection.py# Decision cutoff filtering and latest-version selection
│   │   └── utils/
│   │       ├── datetime_utils.py    # Timezone conversion, DST, and settlement periods
│   │       └── validation.py        # Date and cutoff validation
│   ├── tests/                       # Unit and integration test suite (28 tests)
│   ├── Dockerfile                   # Python 3.11-slim container with health check
│   ├── preload_data.py              # Historical data preloader for January 2026
│   └── requirements.txt             # Pinned backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/              # Modular UI components (TopBar, Chart, Table, etc.)
│   │   ├── services/api.ts          # Typed REST client
│   │   ├── test/                    # Vitest and React Testing Library tests (6 tests)
│   │   ├── types/index.ts           # TypeScript interfaces matching backend models
│   │   ├── App.tsx                  # Main reactive application shell
│   │   └── index.css                # Tailwind directives and typography styling
│   ├── Dockerfile                   # Multi-stage build with Nginx Alpine
│   ├── nginx.conf                   # Nginx reverse proxy and SPA routing
│   └── package.json                 # Pinned frontend dependencies
├── data/cache/                      # Indexed SQLite database (bmrs_cache.db)
├── docs/
│   ├── ARCHITECTURE.md              # System design and sequence diagrams
│   ├── CLIENT_DEMO_SCRIPT.md        # 5-minute client presentation walkthrough
│   ├── TECHNICAL_REVIEW_SCRIPT.md   # 5-minute technical review walkthrough
│   └── FINAL_ACCEPTANCE_CHECKLIST.md# Verification checklist
├── docker-compose.yml               # Complete container orchestration
├── render.yaml                      # Render deployment configuration for backend
├── vercel.json                      # Vercel deployment configuration for frontend
├── .env.example                     # Sample environment variables
└── README.md                        # Primary documentation
```

---

## 14. Prerequisites

- **Python**: Version 3.11+
- **Node.js**: Version 20+ (Node v22 recommended)
- **Git**
- **Docker & Docker Compose** (for containerized execution)

---

## 15. Local Setup Instructions

### Option A: Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone <REPO_URL>
   cd first_project
   ```

2. **Set up and start the Python Backend**:
   ```bash
   python3 -m venv backend/.venv
   source backend/.venv/bin/activate
   pip install -r backend/requirements.txt
   
   # Run the backend server
   PYTHONPATH=backend uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   *The backend API will be running at `http://127.0.0.1:8000` with interactive Swagger docs at `http://127.0.0.1:8000/docs`.*

3. **Set up and start the React Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   *The frontend dashboard will be running at `http://localhost:5173`.*

---

## 16. Environment Variables

Copy `.env.example` to `.env` or set the following in your deployment environment:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `PROJECT_NAME` | `WindScope — UK Wind Forecast Intelligence` | Product title |
| `ELEXON_BASE_URL` | `https://data.elexon.co.uk/bmrs/api/v1` | Official Elexon BMRS API host |
| `DEFAULT_CUTOFF_TIME` | `09:30` | Default decision cutoff time in Europe/London |
| `DEFAULT_TIMEZONE` | `Europe/London` | Primary market timezone |
| `CACHE_ENABLED` | `true` | Enables local SQLite persistent cache |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Allowed CORS origins (supports Vercel wildcard) |
| `VITE_API_URL` | `""` (proxied in dev) | Public backend URL for frontend build |

---

## 17. Docker Instructions

Run the entire platform with a single command:

```bash
docker compose up --build
```

- **Frontend Application**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **Swagger Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/health`

To stop:
```bash
docker compose down
```

---

## 18. Automated Tests & Actual Results

### Backend Test Execution
Executed with `pytest` using Python 3.11:
```bash
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests/ -v
```
**Observed Result**:
- `test_hand_verified_prompt_fixture`: **PASSED** (Forecasts=[100,120,80], Actuals=[90,110,100] $\to$ MAE=13.33, RMSE=14.14, Bias=0)
- `test_mape_excludes_zero_actuals`: **PASSED**
- `test_missing_forecast_does_not_become_zero`: **PASSED**
- `test_empty_dataset_returns_unavailable_state`: **PASSED**
- `test_bias_sign_convention`: **PASSED**
- `test_forecasts_before_at_and_after_cutoff`: **PASSED**
- `test_latest_eligible_selected_when_all_before_cutoff`: **PASSED**
- `test_all_published_after_cutoff_results_in_no_eligible_forecast`: **PASSED**
- `test_duplicate_records_handled_deterministically`: **PASSED**
- `test_matching_by_delivery_timestamp`: **PASSED**
- `test_daylight_saving_transitions` (46 periods spring, 50 periods autumn, 48 standard): **PASSED**
- `test_upstream_timeout_and_retries` (respx mock): **PASSED**
- `test_upstream_500_server_error_retries`: **PASSED**
- `test_api_endpoints` (Health, Overview, Forecast, Records, Accuracy, CSV Export): **PASSED**
- **Summary**: `28 passed in 6.46s`

### Frontend Test Execution
Executed with `vitest` in jsdom:
```bash
cd frontend && npm test
```
**Observed Result**:
- `renders the header and brand identity correctly`: **PASSED**
- `loads and displays overview metrics from API responses`: **PASSED**
- `displays delivery periods and missing observations transparently`: **PASSED**
- `triggers CSV export download upon clicking export button`: **PASSED**
- `opens and closes the methodology modal`: **PASSED**
- `handles API error state gracefully`: **PASSED**
- **Summary**: `6 passed in 1.29s`

### Production Build & Type Checking
```bash
cd frontend && npm run build
```
**Observed Result**: `tsc && vite build` succeeded in 1.87s with zero errors.

### Independent Verification of 10 January 2026 Sample Analysis
Auditing the sample analysis for Decision Date `2026-01-10` and Delivery Date `2026-01-11` (Cutoff: `09:30 Europe/London`):
- **Why MAE and Bias are both +4,948.46 MW**: An audit of all 24 individual matched settlement periods reveals that National Grid ESO's 09:30 morning forecast overestimated actual wind output for every single period ($F_i > A_i$ for all $i \in [1, 24]$). Because every error $e_i \ge 0$, $|e_i| \equiv e_i$, and therefore $\text{MAE} \equiv \text{Bias} = \frac{118,763.00\text{ MW}}{24} = 4,948.4583\text{ MW}$.
- **Underforecasting on Other Days**: Across January 2026, 4 days exhibited net negative bias (underforecast): `2026-01-04` (-28.92 MW), `2026-01-09` (-105.29 MW), `2026-01-13` (-125.25 MW), and `2026-01-18` (-744.38 MW), where $\text{Bias} < 0$ and $\text{MAE} \ne \text{Bias}$.
- **Exclusion of Post-Cutoff Forecasts**: On 10 January 2026, four subsequent WINDFOR publications were issued after 09:30 (at 11:30, 15:30, 18:30, and 22:30). The engine correctly identified and excluded all four, selecting `2026-01-10T09:30:00Z` as the latest eligible publication.

---

## 19. Public Frontend URL

- **Production Frontend**: `https://windscope-app.vercel.app` *(or configured Vercel deployment URL)*
- **Local URL**: `http://localhost:5173` (or `http://localhost:3000` via Docker)

---

## 20. Public Backend & API Documentation URL

- **Production Backend**: `https://windscope-backend.onrender.com` *(or configured Render deployment URL)*
- **Interactive OpenAPI Documentation**: `https://windscope-backend.onrender.com/docs`
- **Health Check**: `https://windscope-backend.onrender.com/api/health`

---

## 21. Deployment Instructions

### Option A: Full-Stack Deployment on Vercel (Frontend + Backend on One Domain)
WindScope is configured to deploy both the React frontend and the Python FastAPI backend directly on Vercel as a single monorepo project:
1. Push this repository to GitHub: `https://github.com/HardikGahlot/WindScope.git`
2. Go to [Vercel Dashboard](https://vercel.com/new) and **Import** the repository.
3. Keep the **Root Directory** as `.` (repo root). Vercel reads `vercel.json` automatically:
   - **Frontend**: Built via `npm run build` (`cd frontend && npm install && npm run build`) into `frontend/dist`.
   - **Backend**: Served via Vercel Serverless Function at `api/index.py` using Python 3.11 with bundled SQLite cache.
   - **Routing**: `/api/*` and `/docs` route to the FastAPI backend; all other routes serve the React SPA.
4. Click **Deploy**. Both the web application and the analytics API will be live on the same Vercel URL with zero CORS configuration required!

### Option B: Deploy Backend to Render (Docker) + Frontend to Vercel
1. In the [Render Dashboard](https://dashboard.render.com), create a **New Web Service**, select Docker environment, set dockerfile path to `./backend/Dockerfile`, context to `.`.
2. Set environment variable `CORS_ORIGINS` to your Vercel URL.
3. In Vercel, set `VITE_API_URL` to your Render backend URL (e.g. `https://windscope-backend.onrender.com`).

### Option C: Heroku Deployment
A `Procfile` (`web: uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`) and `runtime.txt` (`python-3.11.8`) are included for direct Heroku container/buildpack deployment.

---

## 22. Security & Operational Considerations

- **CORS Protection**: Access is restricted to configured frontend domains with regex support for Vercel preview environments.
- **Upstream Resilience**: Upstream requests to Elexon include bounded timeouts and exponential backoff on HTTP 429 and 5xx errors.
- **Information Leakage Prevention**: Production exception handlers intercept internal errors and return generic error responses without exposing server traces or environment variables.
- **Non-Invasive Caching**: Immutable historical datasets for January 2026 are cached locally in SQLite to prevent spamming the Elexon API and guarantee sub-second dashboard rendering.

---

## 23. AI Tools Disclosures

In accordance with hiring assessment submission guidelines:
- **AI Coding Assistant**: Google Antigravity (featuring Gemini 3.8 Flash High) was used during this project for pair programming, test design, and documentation preparation.
- **Role of AI**: The assistant provided codebase structuring, verification test generation against known fixtures, and exploratory API probing. All architecture decisions, domain logic validations, mathematical checks, and test executions were directed and verified against live Elexon data.
