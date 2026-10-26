export type MatchingMode = 'exact' | 'mapped_hourly';

export interface AccuracyMetrics {
  mae: number | null;
  rmse: number | null;
  bias: number | null;
  mape: number | null;
  total_expected_periods: number;
  matched_periods_count: number;
  missing_forecast_count: number;
  missing_actual_count: number;
  mape_excluded_zero_actuals_count: number;
  overforecast_count: number;
  underforecast_count: number;
  exact_match_count: number;
  max_absolute_error_mw: number | null;
  coverage_percentage: number;
  calculation_status: 'valid' | 'insufficient_data' | 'no_matched_pairs';
}

export interface OverviewResponse {
  product_name: string;
  decision_date: string;
  delivery_date: string;
  decision_cutoff_london: string;
  decision_cutoff_utc: string;
  latest_eligible_publish_time_utc: string | null;
  latest_eligible_publish_time_london: string | null;
  expected_wind_generation_avg_mw: number | null;
  actual_wind_generation_avg_mw: number | null;
  expected_wind_generation_peak_mw: number | null;
  actual_wind_generation_peak_mw: number | null;
  metrics: AccuracyMetrics;
  data_source: string;
  retrieval_status: string;
  matching_mode: MatchingMode;
  notes: string[];
}

export interface DecisionTimeForecastRecord {
  delivery_time_utc: string;
  delivery_time_london: string;
  settlement_period: number;
  forecast_generation_mw: number | null;
  publish_time_utc: string | null;
  publish_time_london: string | null;
  cutoff_time_utc: string;
  cutoff_time_london: string;
  is_eligible: boolean;
  selection_status: string;
  candidates_considered_count: number;
  excluded_after_cutoff_count: number;
  data_quality_flags: string[];
}

export interface MatchedDeliveryRecord {
  delivery_time_utc: string;
  delivery_time_london: string;
  settlement_date: string;
  settlement_period: number;
  forecast_generation_mw: number | null;
  actual_generation_mw: number | null;
  error_mw: number | null;
  abs_error_mw: number | null;
  percentage_error: number | null;
  publish_time_utc: string | null;
  publish_time_london: string | null;
  cutoff_time_london: string;
  match_status: 'matched' | 'missing_forecast' | 'missing_actual' | 'both_missing';
  data_quality_flags: string[];
}

export interface ForecastExplorerResponse {
  decision_date: string;
  delivery_date: string;
  decision_cutoff_london: string;
  decision_cutoff_utc: string;
  total_delivery_periods: number;
  matched_forecasts_count: number;
  missing_forecasts_count: number;
  matching_mode: MatchingMode;
  records: DecisionTimeForecastRecord[];
}

export interface DailyTrendItem {
  decision_date: string;
  delivery_date: string;
  mae: number | null;
  rmse: number | null;
  bias: number | null;
  mape: number | null;
  avg_forecast_mw: number | null;
  avg_actual_mw: number | null;
  matched_periods: number;
  total_expected: number;
  coverage_percentage: number;
}

export interface AccuracyAnalysisResponse {
  start_date: string;
  end_date: string;
  decision_cutoff_london: string;
  aggregate_metrics: AccuracyMetrics;
  daily_trends: DailyTrendItem[];
  largest_errors: MatchedDeliveryRecord[];
  notes: string[];
}

export interface RecordsResponse {
  decision_date: string;
  delivery_date: string;
  decision_cutoff_london: string;
  total_records: number;
  matched_records: number;
  missing_forecasts: number;
  missing_actuals: number;
  matching_mode: MatchingMode;
  records: MatchedDeliveryRecord[];
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  timestamp_utc: string;
  upstream_elexon_status: string;
  cache_status: string;
}
