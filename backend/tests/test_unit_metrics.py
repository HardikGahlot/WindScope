import math
import pytest
from app.models.schemas import MatchedDeliveryRecord
from app.services.accuracy_metrics import compute_metrics


def create_record(f: float | None, a: float | None, period: int = 1) -> MatchedDeliveryRecord:
    e = None
    abs_e = None
    pct_e = None
    status = "matched"
    if f is not None and a is not None:
        e = f - a
        abs_e = abs(e)
        if a != 0:
            pct_e = (abs_e / a) * 100.0
    elif f is None and a is not None:
        status = "missing_forecast"
    elif f is not None and a is None:
        status = "missing_actual"
    else:
        status = "both_missing"

    return MatchedDeliveryRecord(
        delivery_time_utc=f"2026-01-02T{period:02d}:00:00Z",
        delivery_time_london=f"2026-01-02 {period:02d}:00 GMT",
        settlement_date="2026-01-02",
        settlement_period=period,
        forecast_generation_mw=f,
        actual_generation_mw=a,
        error_mw=e,
        abs_error_mw=abs_e,
        percentage_error=pct_e,
        publish_time_utc="2026-01-01T09:00:00Z",
        publish_time_london="2026-01-01 09:00 GMT",
        cutoff_time_london="09:30 Europe/London",
        match_status=status,
    )


def test_hand_verified_prompt_fixture():
    """
    Verify exact test fixture from prompt:
    Forecasts = [100, 120, 80]
    Actuals = [90, 110, 100]
    Expected errors = [10, 10, -20]
    Expected MAE = 13.333333...
    Expected RMSE = sqrt(200) = 14.1421356...
    Expected bias = 0
    """
    records = [
        create_record(100.0, 90.0, period=1),
        create_record(120.0, 110.0, period=2),
        create_record(80.0, 100.0, period=3),
    ]
    metrics = compute_metrics(records, total_expected_periods=3)

    assert metrics.matched_periods_count == 3
    assert math.isclose(metrics.mae, 13.3333, abs_tol=1e-3)
    assert math.isclose(metrics.rmse, 14.1421, abs_tol=1e-3)
    assert math.isclose(metrics.bias, 0.0, abs_tol=1e-3)
    assert metrics.overforecast_count == 2
    assert metrics.underforecast_count == 1
    assert metrics.exact_match_count == 0
    assert metrics.max_absolute_error_mw == 20.0
    assert metrics.coverage_percentage == 100.0


def test_mape_excludes_zero_actuals():
    """
    Test 17: MAPE excludes zero actual values and reports exclusions count.
    """
    records = [
        create_record(100.0, 50.0, period=1),   # e = 50, |50/50| = 1.0 -> 100%
        create_record(200.0, 100.0, period=2),  # e = 100, |100/100| = 1.0 -> 100%
        create_record(50.0, 0.0, period=3),     # a == 0 -> excluded from MAPE!
    ]
    metrics = compute_metrics(records, total_expected_periods=3)

    assert metrics.matched_periods_count == 3
    assert metrics.mape_excluded_zero_actuals_count == 1
    # MAPE is computed only over periods 1 and 2: (100% + 100%) / 2 = 100%
    assert math.isclose(metrics.mape, 100.0, abs_tol=1e-3)


def test_missing_forecast_does_not_become_zero():
    """
    Test 10 & 11: Missing forecast and actual values do not become zero.
    """
    records = [
        create_record(100.0, 80.0, period=1),
        create_record(None, 90.0, period=2),  # missing forecast
        create_record(120.0, None, period=3), # missing actual
    ]
    metrics = compute_metrics(records, total_expected_periods=3)

    # Only 1 pair is fully valid
    assert metrics.matched_periods_count == 1
    assert metrics.missing_forecast_count == 1
    assert metrics.missing_actual_count == 1
    # MAE should be computed from the 1 valid pair (100 - 80 = 20), NOT treating missing as 0!
    assert metrics.mae == 20.0
    assert metrics.rmse == 20.0
    assert metrics.bias == 20.0


def test_empty_dataset_returns_unavailable_state():
    """
    Test 18: Empty datasets return valid unavailable states (null metrics).
    """
    records = []
    metrics = compute_metrics(records, total_expected_periods=48)

    assert metrics.matched_periods_count == 0
    assert metrics.mae is None
    assert metrics.rmse is None
    assert metrics.bias is None
    assert metrics.mape is None
    assert metrics.coverage_percentage == 0.0
    assert metrics.calculation_status == "no_matched_pairs"


def test_bias_sign_convention():
    """
    Test 16: Bias has correct sign:
    Positive = forecast overestimated actual wind generation.
    Negative = forecast underestimated actual wind generation.
    """
    # Overforecasting case
    rec_over = [create_record(150.0, 100.0)]
    m_over = compute_metrics(rec_over, total_expected_periods=1)
    assert m_over.bias == 50.0
    assert m_over.overforecast_count == 1
    assert m_over.underforecast_count == 0

    # Underforecasting case
    rec_under = [create_record(80.0, 100.0)]
    m_under = compute_metrics(rec_under, total_expected_periods=1)
    assert m_under.bias == -20.0
    assert m_under.underforecast_count == 1
    assert m_under.overforecast_count == 0
