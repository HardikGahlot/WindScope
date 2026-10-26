from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class RawFuelHHRecord(BaseModel):
    dataset: str = "FUELHH"
    publishTime: Optional[str] = None
    startTime: str
    settlementDate: Optional[str] = None
    settlementPeriod: Optional[int] = None
    fuelType: str
    generation: Optional[float] = None


class RawWindforRecord(BaseModel):
    dataset: str = "WINDFOR"
    publishTime: str
    startTime: str
    generation: Optional[float] = None


class DecisionTimeForecastRecord(BaseModel):
    delivery_time_utc: str
    delivery_time_london: str
    settlement_period: int
    forecast_generation_mw: Optional[float] = None
    publish_time_utc: Optional[str] = None
    publish_time_london: Optional[str] = None
    cutoff_time_utc: str
    cutoff_time_london: str
    is_eligible: bool
    selection_status: str  # "selected", "no_eligible_forecast", "missing_in_source"
    candidates_considered_count: int = 0
    excluded_after_cutoff_count: int = 0
    data_quality_flags: List[str] = Field(default_factory=list)


class MatchedDeliveryRecord(BaseModel):
    delivery_time_utc: str
    delivery_time_london: str
    settlement_date: str
    settlement_period: int
    forecast_generation_mw: Optional[float] = None
    actual_generation_mw: Optional[float] = None
    error_mw: Optional[float] = None  # F - A (positive: overforecast, negative: underforecast)
    abs_error_mw: Optional[float] = None  # |F - A|
    percentage_error: Optional[float] = None  # |(F - A)/A| * 100 when A != 0
    publish_time_utc: Optional[str] = None
    publish_time_london: Optional[str] = None
    cutoff_time_london: str
    match_status: str  # "matched", "missing_forecast", "missing_actual", "both_missing"
    data_quality_flags: List[str] = Field(default_factory=list)


class AccuracyMetrics(BaseModel):
    mae: Optional[float] = None
    rmse: Optional[float] = None
    bias: Optional[float] = None  # mean(F - A)
    mape: Optional[float] = None  # mean(|(F - A) / A|) * 100
    total_expected_periods: int
    matched_periods_count: int
    missing_forecast_count: int
    missing_actual_count: int
    mape_excluded_zero_actuals_count: int
    overforecast_count: int  # error > 0
    underforecast_count: int  # error < 0
    exact_match_count: int  # error == 0
    max_absolute_error_mw: Optional[float] = None
    coverage_percentage: float
    calculation_status: str  # "valid", "insufficient_data", "no_matched_pairs"


class DailyTrendItem(BaseModel):
    decision_date: str
    delivery_date: str
    mae: Optional[float] = None
    rmse: Optional[float] = None
    bias: Optional[float] = None
    mape: Optional[float] = None
    avg_forecast_mw: Optional[float] = None
    avg_actual_mw: Optional[float] = None
    matched_periods: int
    total_expected: int
    coverage_percentage: float


class OverviewResponse(BaseModel):
    product_name: str = "WindScope — UK Wind Forecast Intelligence"
    decision_date: str
    delivery_date: str
    decision_cutoff_london: str
    decision_cutoff_utc: str
    latest_eligible_publish_time_utc: Optional[str] = None
    latest_eligible_publish_time_london: Optional[str] = None
    expected_wind_generation_avg_mw: Optional[float] = None
    actual_wind_generation_avg_mw: Optional[float] = None
    expected_wind_generation_peak_mw: Optional[float] = None
    actual_wind_generation_peak_mw: Optional[float] = None
    metrics: AccuracyMetrics
    data_source: str = "Elexon BMRS (FUELHH and WINDFOR)"
    retrieval_status: str = "success"
    matching_mode: str = "exact"  # "exact" or "mapped_hourly"
    notes: List[str] = Field(default_factory=list)


class ForecastExplorerResponse(BaseModel):
    decision_date: str
    delivery_date: str
    decision_cutoff_london: str
    decision_cutoff_utc: str
    total_delivery_periods: int
    matched_forecasts_count: int
    missing_forecasts_count: int
    matching_mode: str
    records: List[DecisionTimeForecastRecord]


class AccuracyAnalysisResponse(BaseModel):
    start_date: str
    end_date: str
    decision_cutoff_london: str
    aggregate_metrics: AccuracyMetrics
    daily_trends: List[DailyTrendItem]
    largest_errors: List[MatchedDeliveryRecord]
    notes: List[str] = Field(default_factory=list)


class RecordsResponse(BaseModel):
    decision_date: str
    delivery_date: str
    decision_cutoff_london: str
    total_records: int
    matched_records: int
    missing_forecasts: int
    missing_actuals: int
    matching_mode: str
    records: List[MatchedDeliveryRecord]


class HealthCheckResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp_utc: str
    upstream_elexon_status: str
    cache_status: str
