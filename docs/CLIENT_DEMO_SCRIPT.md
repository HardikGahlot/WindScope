# Client Presentation Demo Script — WindScope
**Target Audience**: Commercial Directors, Energy Trading Managers, Wholesale Power Buyers  
**Estimated Duration**: ~5 minutes

---

### [00:00 - 00:45] 1. The Business Problem & Market Context
**Speaker**:  
> "Good morning. As a UK electricity utility purchasing power on the wholesale market, our core challenge every morning is purchasing electricity for delivery tomorrow. 
> 
> Because wind output is weather-dependent and volatile, our procurement decisions depend heavily on wind forecasts. However, when making purchasing decisions ahead of market auction deadlines—for example, at 09:30 or 11:00 in the morning—our trading desk can only act upon forecasts that have **already been published** by National Grid ESO.
> 
> The platform you are looking at is **WindScope**, built specifically to give commercial teams complete visibility into the wind generation forecast that was actually known at decision time, and to benchmark that forecast against real physical delivery outturns from Elexon BMRS."

---

### [00:45 - 01:45] 2. The Decision-Time Forecast Explorer & Why Publication Time Matters
**Action**: Direct attention to the Top Controls bar. Select **Decision Date: 10 January 2026** and show **Delivery Date: 11 January 2026 (Day-Ahead)**.
**Speaker**:  
> "Notice the controls at the top. On the wholesale market, a decision made on **10 January 2026** purchases power for physical delivery on **11 January 2026**. 
> 
> Here is why publication timestamps are critical: throughout the day, the transmission system operator issues updated wind forecasts every few hours. If an analytics dashboard naively pulls the 'latest available forecast' or forecasts published at 14:00 or 18:00, it introduces **lookahead bias**. A trader sitting at their desk at 09:30 could not have seen an afternoon update.
> 
> WindScope's selection engine enforces an inclusive cutoff rule. Looking at the provenance ribbon, on 10 January at our 09:30 cutoff, the latest eligible forecast was published at **09:30 GMT**. Any forecasts published after that deadline are strictly excluded."

---

### [01:45 - 03:00] 3. Forecast vs. Actual Generation & Accuracy KPIs
**Action**: Point to Executive KPI cards and the **Forecast vs Actual Delivery Profile** chart.
**Speaker**:  
> "Looking at the Executive Overview for delivery on 11 January:
> - **Expected Generation**: Our decision-time forecast predicted an average output of **18,454 MW**, peaking over **20,300 MW**.
> - **Actual Outturn**: The real physical wind output recorded by Elexon averaged **13,557 MW**, peaking at only **16,018 MW**.
> 
> The consequence is immediately visible in our accuracy metrics:
> - **Mean Absolute Error (MAE)**: **4,948 MW**. On average, each half-hour delivery period deviated by nearly 5 gigawatts.
> - **Forecast Bias**: **+4,948 MW**. The positive sign is vital—it proves that on this delivery day, the forecast consistently **overestimated** actual wind generation across all 24 periods. 
> 
> In procurement terms, if our buyers had relied uncritically on this morning forecast, our portfolio would have been materially short on physical wind infeed, requiring costly intraday or balancing mechanism purchases."

---

### [03:00 - 04:00] 4. Missing-Data Transparency & Settlement Resolution
**Action**: Switch to the **Audit Records Table** tab or point to the chart gaps.
**Speaker**:  
> "Now let's address data integrity. In the UK market, settlement periods are half-hourly—48 periods per day. However, National Grid publishes WINDFOR forecasts at **hourly** intervals (:00).
> 
> Many commercial platforms quietly hide this by interpolating or inventing half-hourly numbers, or treating missing periods as zero. WindScope never does this.
> 
> In **Exact Resolution Mode**, we show clear visual gaps for the :30 periods. Our table explicitly flags them as `Hourly WINDFOR (:30 gap)`. Furthermore, our MAPE metric explicitly excludes periods with zero actual generation so percentage calculations are never corrupted by division by zero.
> 
> If our portfolio team prefers an operational block-hour approximation, they can click **Mapped Block Hour** to project the hourly forecast across both half-hours—with every mapped observation clearly labeled in the audit trail."

---

### [04:00 - 05:00] 5. Monthly Trends, Governance & Commercial Next Steps
**Action**: Switch to **January 2026 Accuracy Trends** tab, and show the **Export CSV** button.
**Speaker**:  
> "Zooming out to the full month of January 2026:
> Across all 31 decision days, WindScope tracks daily MAE and Bias. Notice that while mid-January saw severe overforecasting biases, late January showed much tighter alignment.
> 
> With a single click on **Export CSV**, our compliance and risk teams can download a full, uncorrupted audit ledger with all timestamps, cutoff contexts, and data quality flags for regulatory reporting.
> 
> **Important Domain Limitation**: We must note that wind forecast error alone does not dictate our exact net power purchases—total consumer demand, solar output, and thermal availability must also be factored in. WindScope provides the definitive, defensible foundation for the wind component of that procurement strategy.
> 
> Thank you. I welcome your questions."
