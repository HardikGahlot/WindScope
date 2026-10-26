from datetime import date
import pytest
from app.models.schemas import RawFuelHHRecord, RawWindforRecord
from app.services.forecast_selection import match_forecast_with_actuals, select_decision_time_forecasts


def test_forecasts_before_at_and_after_cutoff():
    """
    Test 1, 2, 3:
    - Forecasts published before cutoff are eligible.
    - Forecasts published exactly at cutoff follow inclusive-boundary rule.
    - Forecasts published after cutoff are excluded.
    """
    decision_date = date(2026, 1, 1)
    delivery_date = date(2026, 1, 2)
    cutoff_time = "09:30"
    delivery_target = "2026-01-02T12:00:00Z"

    # Three publications for the same delivery target:
    # 1. 07:30 (before cutoff)
    # 2. 09:30 (exact cutoff boundary)
    # 3. 11:30 (after cutoff)
    records = [
        RawWindforRecord(publishTime="2026-01-01T07:30:00Z", startTime=delivery_target, generation=5000.0),
        RawWindforRecord(publishTime="2026-01-01T09:30:00Z", startTime=delivery_target, generation=5500.0),
        RawWindforRecord(publishTime="2026-01-01T11:30:00Z", startTime=delivery_target, generation=6000.0),
    ]

    selected = select_decision_time_forecasts(
        windfor_records=records,
        decision_date=decision_date,
        delivery_date=delivery_date,
        cutoff_time_str=cutoff_time,
        matching_mode="exact",
    )

    # Find the record for 12:00:00Z
    rec_12 = next(r for r in selected if r.delivery_time_utc == delivery_target)

    # Must select 09:30 (exact inclusive cutoff boundary) with 5500.0 MW
    assert rec_12.forecast_generation_mw == 5500.0
    assert rec_12.publish_time_utc == "2026-01-01T09:30:00Z"
    assert rec_12.is_eligible is True
    assert rec_12.selection_status == "selected"
    assert rec_12.candidates_considered_count == 3
    # 1 candidate (11:30) was excluded after cutoff
    assert rec_12.excluded_after_cutoff_count == 1


def test_latest_eligible_selected_when_all_before_cutoff():
    """
    Test 4 & 5:
    The latest eligible forecast is selected among multiple publication versions.
    """
    decision_date = date(2026, 1, 1)
    delivery_date = date(2026, 1, 2)
    cutoff_time = "09:30"
    delivery_target = "2026-01-02T14:00:00Z"

    records = [
        RawWindforRecord(publishTime="2026-01-01T02:30:00Z", startTime=delivery_target, generation=4000.0),
        RawWindforRecord(publishTime="2026-01-01T04:30:00Z", startTime=delivery_target, generation=4200.0),
        RawWindforRecord(publishTime="2026-01-01T07:30:00Z", startTime=delivery_target, generation=4500.0),
    ]

    selected = select_decision_time_forecasts(
        windfor_records=records,
        decision_date=decision_date,
        delivery_date=delivery_date,
        cutoff_time_str=cutoff_time,
    )

    rec_14 = next(r for r in selected if r.delivery_time_utc == delivery_target)
    assert rec_14.forecast_generation_mw == 4500.0
    assert rec_14.publish_time_utc == "2026-01-01T07:30:00Z"
    assert rec_14.candidates_considered_count == 3
    assert rec_14.excluded_after_cutoff_count == 0


def test_all_published_after_cutoff_results_in_no_eligible_forecast():
    """
    If candidates exist but ALL were published after the cutoff, none should be selected.
    """
    decision_date = date(2026, 1, 1)
    delivery_date = date(2026, 1, 2)
    cutoff_time = "06:00"  # cutoff is 06:00
    delivery_target = "2026-01-02T10:00:00Z"

    records = [
        RawWindforRecord(publishTime="2026-01-01T07:30:00Z", startTime=delivery_target, generation=8000.0),
        RawWindforRecord(publishTime="2026-01-01T09:30:00Z", startTime=delivery_target, generation=8200.0),
    ]

    selected = select_decision_time_forecasts(
        windfor_records=records,
        decision_date=decision_date,
        delivery_date=delivery_date,
        cutoff_time_str=cutoff_time,
    )

    rec = next(r for r in selected if r.delivery_time_utc == delivery_target)
    assert rec.forecast_generation_mw is None
    assert rec.is_eligible is False
    assert rec.selection_status == "no_eligible_forecast"
    assert rec.candidates_considered_count == 2
    assert rec.excluded_after_cutoff_count == 2
    assert "ALL_CANDIDATES_PUBLISHED_AFTER_CUTOFF" in rec.data_quality_flags


def test_duplicate_records_handled_deterministically():
    """
    Test 12: Duplicate records with same publish and start time are handled deterministically.
    """
    decision_date = date(2026, 1, 1)
    delivery_date = date(2026, 1, 2)
    cutoff_time = "09:30"
    delivery_target = "2026-01-02T15:00:00Z"

    records = [
        RawWindforRecord(publishTime="2026-01-01T08:00:00Z", startTime=delivery_target, generation=3000.0),
        RawWindforRecord(publishTime="2026-01-01T08:00:00Z", startTime=delivery_target, generation=3000.0),
    ]

    selected = select_decision_time_forecasts(
        windfor_records=records,
        decision_date=decision_date,
        delivery_date=delivery_date,
        cutoff_time_str=cutoff_time,
    )

    rec = next(r for r in selected if r.delivery_time_utc == delivery_target)
    assert rec.forecast_generation_mw == 3000.0
    assert "DUPLICATE_PUBLICATION_RESOLVED" in rec.data_quality_flags


def test_matching_by_delivery_timestamp():
    """
    Test 6: Records are matched by exact delivery timestamp against FUELHH actuals.
    """
    delivery_date = date(2026, 1, 2)
    decision_date = date(2026, 1, 1)

    wind_records = [
        RawWindforRecord(publishTime="2026-01-01T08:00:00Z", startTime="2026-01-02T10:00:00Z", generation=12000.0),
    ]
    actual_records = [
        RawFuelHHRecord(startTime="2026-01-02T10:00:00Z", fuelType="WIND", generation=11500.0),
        RawFuelHHRecord(startTime="2026-01-02T10:00:00Z", fuelType="NUCLEAR", generation=5000.0),  # non-wind ignored
    ]

    selected = select_decision_time_forecasts(
        windfor_records=wind_records,
        decision_date=decision_date,
        delivery_date=delivery_date,
        cutoff_time_str="09:30",
    )
    matched = match_forecast_with_actuals(selected, actual_records, delivery_date, "09:30")

    rec_10 = next(r for r in matched if r.delivery_time_utc == "2026-01-02T10:00:00Z")
    assert rec_10.forecast_generation_mw == 12000.0
    assert rec_10.actual_generation_mw == 11500.0
    assert rec_10.error_mw == 500.0  # 12000 - 11500
    assert rec_10.match_status == "matched"
