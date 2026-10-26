# Technical Architecture & Engineering Review Script — WindScope
**Target Audience**: Lead Software Engineers, System Architects, Technical Assessors  
**Estimated Duration**: ~5 minutes

---

### [00:00 - 01:00] 1. Architecture, Stack & Design Philosophy
**Speaker**:  
> "Hello. Welcome to the technical review of **WindScope**.
> 
> Our architectural objective was to deliver a production-grade, statistically sound intelligence service with zero lookahead bias and absolute data integrity.
> 
> The system is architected as:
> 1. **Backend**: Python 3.11 with **FastAPI**, **Pydantic v2**, and **httpx**. We prioritized type safety, explicit schemas, and clean separation between the Elexon communication layer, the time-semantics engine, and the analytics service.
> 2. **Frontend**: **React 18** and **TypeScript** configured in strict mode, bundled with **Vite**, styled with a dark enterprise **Tailwind CSS** theme, and visualized with **Recharts**.
> 3. **Data Layer**: An indexed **SQLite** persistent store (`bmrs_cache.db`) paired with an in-memory cache to ensure sub-millisecond API response times and 100% offline reproducibility without external database bloat."

---

### [01:00 - 02:00] 2. Elexon Integration & Retrospective Selection Algorithm
**Speaker**:  
> "Let's examine how we interface with the official Elexon BMRS API.
> 
> We pull two core streams:
> - `FUELHH/stream` for half-hourly generation outturn by fuel type, filtering strictly on `fuelType = 'WIND'`.
> - `WINDFOR/stream` for wind generation forecasts.
> 
> **Why a 'latest forecast' endpoint fails**:
> A common flaw in naive implementations is querying an endpoint that returns only the latest forecast snapshot. That introduces fatal lookahead bias. To reconstruct the forecast as known at 09:30 on 10 January, we query `WINDFOR/stream` with `publishDateTimeFrom` and `publishDateTimeTo` parameters. This retrieves the complete publication history.
> 
> In `app/services/forecast_selection.py`, our selection algorithm operates as follows:
> 1. It localizes the decision date and cutoff (e.g., 09:30) to `Europe/London` and converts it to a UTC boundary timestamp.
> 2. For each delivery period, it evaluates all candidate WINDFOR records targeting that period.
> 3. It filters candidates with an **inclusive boundary**: `publishTime <= cutoff_utc`. Any forecast published strictly after the cutoff is recorded in `excluded_after_cutoff_count` and discarded.
> 4. Among eligible candidates, it selects the record with the maximum `publishTime`.
> 5. Provenance flags, candidate counts, and publication timestamps are attached to each record."

---

### [02:00 - 03:00] 3. Timezone Normalization & Resolution Mismatch
**Speaker**:  
> "Let's look at `app/utils/datetime_utils.py` and our handling of time semantics.
> 
> 1. **Timezone Awareness**: All timestamps from Elexon are parsed into timezone-aware UTC `datetime` objects. All mathematical and chronological comparisons (`<=`, `max()`) are performed strictly in UTC. They are localized to `Europe/London` only for presentation.
> 2. **Daylight Saving Safety**: We use Python's native `zoneinfo.ZoneInfo("Europe/London")`. Our settlement period generator dynamically handles the 46-period spring transition (23 hours), 50-period autumn transition (25 hours), and standard 48-period days.
> 3. **Hourly vs Half-Hourly Resolution**: In the raw Elexon API, WINDFOR forecasts are hourly (`:00`), whereas FUELHH actuals are half-hourly (`:00` and `:30`).
> Rather than silently interpolating or replacing `:30` periods with zero, WindScope defaults to **Exact Resolution**: 24 periods match, while the 24 half-hourly periods are flagged as `HOURLY_RESOLUTION_NO_EXACT_HALF_HOUR_FORECAST` and rendered as clean visual gaps using Recharts `connectNulls={false}`. We also provide an optional `mapped_hourly` mode for operational block-hour evaluation."

---

### [03:00 - 04:00] 4. Statistically Correct Metrics Implementation
**Speaker**:  
> "Let's review `app/services/accuracy_metrics.py`. We implemented four primary metrics according to strict mathematical definitions:
> - **Error Definition**: $e = F - A$. A positive error indicates an overforecast; a negative error indicates an underforecast.
> - **Mean Absolute Error (MAE)**: $\frac{1}{N} \sum |F - A|$.
> - **Root Mean Squared Error (RMSE)**: $\sqrt{\frac{1}{N} \sum (F - A)^2}$.
> - **Mean Forecast Bias**: $\frac{1}{N} \sum (F - A)$.
> - **MAPE**: $\frac{1}{M} \sum |\frac{F - A}{A}| \times 100$.
> 
> **Zero & Missing Handling**:
> Missing forecasts or actuals are **never treated as zero**. They are excluded from the metric denominator, and their exact counts are reported. Furthermore, if an actual observation is $0\text{ MW}$, it is strictly excluded from the MAPE denominator to avoid division by zero, and `mape_excluded_zero_actuals_count` is incremented.
> 
> If $N = 0$, the calculation returns `null` with status `no_matched_pairs` rather than inventing placeholder numbers."

---

### [04:00 - 05:00] 5. Testing, Docker & Operational Readiness
**Speaker**:  
> "Finally, let's look at quality assurance and deployment:
> 
> 1. **Testing**:
>    - **Backend**: 28 automated tests covering inclusive cutoff rules, timestamp matching, DST handling, duplicate resolution, error sign conventions, CSV formatting, and mocked Elexon client behaviors (using `respx` to test 429 rate limiting, 500 server errors, and timeouts). Hand-verified fixtures validate known values: $F=[100, 120, 80], A=[90, 110, 100] \implies \text{MAE}=13.33, \text{RMSE}=14.14, \text{Bias}=0.0$.
>    - **Frontend**: 6 component and integration tests with Vitest and React Testing Library covering rendering, metric binding, modal controls, and CSV export.
>    - **Type Check**: Clean TypeScript compilation (`tsc && vite build`) with zero linting or type errors.
> 2. **Docker**:
>    - Multi-stage frontend Dockerfile with lean Nginx alpine.
>    - Python 3.11-slim backend Dockerfile with health checks.
>    - Reproducible `docker-compose.yml` startup with configured CORS and environment variables.
> 3. **Public Deployment**:
>    - Configured for Vercel (frontend) via `vercel.json` and Render (backend) via `render.yaml`.
> 
> This completes the technical walkthrough. The architecture is modular, defensible, and ready for production deployment."
