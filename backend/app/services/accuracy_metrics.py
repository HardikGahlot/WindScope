import math
from typing import List, Optional, Tuple
from app.models.schemas import AccuracyMetrics, MatchedDeliveryRecord


def compute_metrics(
    records: List[MatchedDeliveryRecord],
    total_expected_periods: int,
) -> AccuracyMetrics:
    """
    Compute statistically rigorous forecast accuracy metrics from matched delivery records.
    
    Let:
      F = forecast generation in MW
      A = actual generation in MW
      e = F - A
      N = number of valid, matched forecast-actual pairs
      
    - MAE = mean(abs(F - A))
    - RMSE = sqrt(mean((F - A)**2))
    - Bias = mean(F - A) (Positive: overforecast, Negative: underforecast)
    - MAPE = mean(abs((F - A) / A)) * 100, strictly excluding A == 0
    
    Strict rules:
    - Missing or invalid pairs are NOT treated as zero.
    - Zero actuals are excluded from MAPE, and their count is explicitly reported.
    - If N == 0, metrics return None with status 'no_matched_pairs'.
    """
    valid_pairs: List[Tuple[float, float, float]] = []  # (F, A, e)
    missing_forecast_count = 0
    missing_actual_count = 0
    
    for r in records:
        f = r.forecast_generation_mw
        a = r.actual_generation_mw
        
        has_f = f is not None and not math.isnan(f)
        has_a = a is not None and not math.isnan(a)
        
        if has_f and has_a:
            e = f - a
            valid_pairs.append((f, a, e))
        else:
            if not has_f:
                missing_forecast_count += 1
            if not has_a:
                missing_actual_count += 1
                
    n = len(valid_pairs)
    coverage_pct = round((n / total_expected_periods * 100.0), 2) if total_expected_periods > 0 else 0.0
    
    if n == 0:
        return AccuracyMetrics(
            mae=None,
            rmse=None,
            bias=None,
            mape=None,
            total_expected_periods=total_expected_periods,
            matched_periods_count=0,
            missing_forecast_count=missing_forecast_count,
            missing_actual_count=missing_actual_count,
            mape_excluded_zero_actuals_count=0,
            overforecast_count=0,
            underforecast_count=0,
            exact_match_count=0,
            max_absolute_error_mw=None,
            coverage_percentage=coverage_pct,
            calculation_status="no_matched_pairs",
        )
        
    abs_errors = [abs(e) for _, _, e in valid_pairs]
    sq_errors = [e ** 2 for _, _, e in valid_pairs]
    raw_errors = [e for _, _, e in valid_pairs]
    
    mae = sum(abs_errors) / n
    rmse = math.sqrt(sum(sq_errors) / n)
    bias = sum(raw_errors) / n
    max_abs_error = max(abs_errors)
    
    overforecast_count = sum(1 for e in raw_errors if e > 0)
    underforecast_count = sum(1 for e in raw_errors if e < 0)
    exact_match_count = sum(1 for e in raw_errors if e == 0)
    
    # MAPE calculation: exclude actual == 0
    mape_entries: List[float] = []
    excluded_zero_actuals = 0
    
    for f, a, e in valid_pairs:
        if abs(a) < 1e-9:  # Effectively zero
            excluded_zero_actuals += 1
        else:
            mape_entries.append(abs(e / a))
            
    if len(mape_entries) > 0:
        mape = (sum(mape_entries) / len(mape_entries)) * 100.0
    else:
        mape = None  # All actuals were zero, MAPE undefined
        
    calc_status = "valid" if n >= (total_expected_periods // 2) else "insufficient_data"
    
    return AccuracyMetrics(
        mae=round(mae, 4),
        rmse=round(rmse, 4),
        bias=round(bias, 4),
        mape=round(mape, 4) if mape is not None else None,
        total_expected_periods=total_expected_periods,
        matched_periods_count=n,
        missing_forecast_count=missing_forecast_count,
        missing_actual_count=missing_actual_count,
        mape_excluded_zero_actuals_count=excluded_zero_actuals,
        overforecast_count=overforecast_count,
        underforecast_count=underforecast_count,
        exact_match_count=exact_match_count,
        max_absolute_error_mw=round(max_abs_error, 2),
        coverage_percentage=coverage_pct,
        calculation_status=calc_status,
    )
