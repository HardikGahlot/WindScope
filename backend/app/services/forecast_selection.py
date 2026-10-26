from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
from app.models.schemas import DecisionTimeForecastRecord, MatchedDeliveryRecord, RawFuelHHRecord, RawWindforRecord
from app.utils.datetime_utils import (
    LONDON_TZ,
    UTC_TZ,
    compute_cutoff_datetime_utc,
    format_iso_utc,
    get_expected_settlement_periods_for_date,
    get_settlement_period_from_datetime,
    parse_iso_utc,
    to_london_display,
)


def select_decision_time_forecasts(
    windfor_records: List[RawWindforRecord],
    decision_date: date,
    delivery_date: date,
    cutoff_time_str: str,
    matching_mode: str = "exact",
) -> List[DecisionTimeForecastRecord]:
    """
    Execute decision-time forecast selection for all settlement periods of the delivery date.
    
    Algorithm:
    1. Compute the cutoff datetime in UTC for the decision date.
    2. Filter candidates matching each settlement period delivery timestamp.
    3. Exclude records published strictly after the cutoff (publishTime > cutoff_utc).
    4. Among remaining eligible records, select the one with the maximum publishTime.
    5. In 'exact' mode: only exact delivery timestamp matches are selected.
       In 'mapped_hourly' mode: :30 periods inherit the forecast for :00 of that same hour.
    6. Record candidate count, exclusion count, and provenance flags.
    """
    cutoff_dt_utc = compute_cutoff_datetime_utc(decision_date, cutoff_time_str)
    cutoff_iso_utc = format_iso_utc(cutoff_dt_utc)
    cutoff_london_str = to_london_display(cutoff_dt_utc)
    
    # Pre-parse and group WINDFOR records by delivery startTime (UTC ISO)
    # startTime in WINDFOR is delivery start
    records_by_start: Dict[str, List[Tuple[datetime, RawWindforRecord]]] = {}
    for r in windfor_records:
        try:
            start_dt = parse_iso_utc(r.startTime)
            pub_dt = parse_iso_utc(r.publishTime)
            start_key = format_iso_utc(start_dt)
            records_by_start.setdefault(start_key, []).append((pub_dt, r))
        except Exception:
            continue  # Invalid record skipped
            
    expected_periods = get_expected_settlement_periods_for_date(delivery_date)
    results: List[DecisionTimeForecastRecord] = []
    
    for period_num, period_start_utc, period_start_london in expected_periods:
        delivery_key = format_iso_utc(period_start_utc)
        delivery_london_str = to_london_display(period_start_utc)
        
        candidates = records_by_start.get(delivery_key, [])
        is_half_hour_offset = (period_start_utc.minute == 30)
        is_mapped = False
        
        # If in mapped_hourly mode and no direct candidate for :30, look up :00 of the same hour
        if not candidates and is_half_hour_offset and matching_mode == "mapped_hourly":
            hour_start_utc = period_start_utc.replace(minute=0, second=0)
            hour_key = format_iso_utc(hour_start_utc)
            candidates = records_by_start.get(hour_key, [])
            is_mapped = True
            
        total_candidates = len(candidates)
        eligible = [(pub_dt, r) for pub_dt, r in candidates if pub_dt <= cutoff_dt_utc]
        excluded_count = total_candidates - len(eligible)
        
        quality_flags: List[str] = []
        if is_half_hour_offset and matching_mode == "exact":
            quality_flags.append("HOURLY_RESOLUTION_NO_EXACT_HALF_HOUR_FORECAST")
        elif is_mapped:
            quality_flags.append("MAPPED_FROM_HOURLY_FORECAST")
            
        if not eligible:
            status = "no_eligible_forecast" if total_candidates > 0 else "missing_in_source"
            if total_candidates > 0 and len(eligible) == 0:
                quality_flags.append("ALL_CANDIDATES_PUBLISHED_AFTER_CUTOFF")
                
            results.append(
                DecisionTimeForecastRecord(
                    delivery_time_utc=delivery_key,
                    delivery_time_london=delivery_london_str,
                    settlement_period=period_num,
                    forecast_generation_mw=None,
                    publish_time_utc=None,
                    publish_time_london=None,
                    cutoff_time_utc=cutoff_iso_utc,
                    cutoff_time_london=cutoff_london_str,
                    is_eligible=False,
                    selection_status=status,
                    candidates_considered_count=total_candidates,
                    excluded_after_cutoff_count=excluded_count,
                    data_quality_flags=quality_flags,
                )
            )
            continue
            
        # Select latest published eligible forecast
        # Sort by pub_dt ascending, last item is latest
        eligible.sort(key=lambda item: item[0])
        best_pub_dt, best_record = eligible[-1]
        
        # Check for multiple records with identical publish timestamp
        same_pub_count = sum(1 for pub_dt, _ in eligible if pub_dt == best_pub_dt)
        if same_pub_count > 1:
            quality_flags.append("DUPLICATE_PUBLICATION_RESOLVED")
            
        results.append(
            DecisionTimeForecastRecord(
                delivery_time_utc=delivery_key,
                delivery_time_london=delivery_london_str,
                settlement_period=period_num,
                forecast_generation_mw=best_record.generation,
                publish_time_utc=format_iso_utc(best_pub_dt),
                publish_time_london=to_london_display(best_pub_dt),
                cutoff_time_utc=cutoff_iso_utc,
                cutoff_time_london=cutoff_london_str,
                is_eligible=True,
                selection_status="selected",
                candidates_considered_count=total_candidates,
                excluded_after_cutoff_count=excluded_count,
                data_quality_flags=quality_flags,
            )
        )
        
    return results


def match_forecast_with_actuals(
    selected_forecasts: List[DecisionTimeForecastRecord],
    actual_records: List[RawFuelHHRecord],
    delivery_date: date,
    cutoff_time_str: str,
) -> List[MatchedDeliveryRecord]:
    """
    Match selected decision-time forecasts with actual wind generation (FUELHH).
    
    Fields matched by exact delivery startTime.
    Error e = F - A
    - Positive: forecast overestimated actual wind generation.
    - Negative: forecast underestimated actual wind generation.
    """
    # Group actuals by delivery timestamp (WIND only)
    actuals_by_start: Dict[str, RawFuelHHRecord] = {}
    for r in actual_records:
        if r.fuelType != "WIND":
            continue
        try:
            start_dt = parse_iso_utc(r.startTime)
            start_key = format_iso_utc(start_dt)
            actuals_by_start[start_key] = r
        except Exception:
            continue
            
    matched_records: List[MatchedDeliveryRecord] = []
    
    for fc in selected_forecasts:
        delivery_key = fc.delivery_time_utc
        actual_r = actuals_by_start.get(delivery_key)
        
        has_f = fc.forecast_generation_mw is not None
        has_a = actual_r is not None and actual_r.generation is not None
        
        flags = list(fc.data_quality_flags)
        f_val = fc.forecast_generation_mw if has_f else None
        a_val = actual_r.generation if has_a else None
        
        error_mw = None
        abs_error_mw = None
        percentage_error = None
        
        if has_f and has_a:
            match_status = "matched"
            error_mw = round(f_val - a_val, 2)
            abs_error_mw = round(abs(error_mw), 2)
            if abs(a_val) > 1e-9:
                percentage_error = round((abs_error_mw / a_val) * 100.0, 2)
            else:
                flags.append("ZERO_ACTUAL_EXCLUDED_FROM_MAPE")
        elif has_f and not has_a:
            match_status = "missing_actual"
            flags.append("ACTUAL_DATA_MISSING")
        elif not has_f and has_a:
            match_status = "missing_forecast"
            flags.append("FORECAST_DATA_MISSING")
        else:
            match_status = "both_missing"
            flags.append("BOTH_FORECAST_AND_ACTUAL_MISSING")
            
        matched_records.append(
            MatchedDeliveryRecord(
                delivery_time_utc=delivery_key,
                delivery_time_london=fc.delivery_time_london,
                settlement_date=delivery_date.isoformat(),
                settlement_period=fc.settlement_period,
                forecast_generation_mw=f_val,
                actual_generation_mw=a_val,
                error_mw=error_mw,
                abs_error_mw=abs_error_mw,
                percentage_error=percentage_error,
                publish_time_utc=fc.publish_time_utc,
                publish_time_london=fc.publish_time_london,
                cutoff_time_london=fc.cutoff_time_london,
                match_status=match_status,
                data_quality_flags=flags,
            )
        )
        
    return matched_records
