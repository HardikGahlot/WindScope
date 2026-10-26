from datetime import date, datetime, timezone
import pytest
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


def test_utc_and_london_conversions():
    """
    Test 7 & 8: Timezone-aware timestamps compare correctly and convert between UTC and London.
    In January, London is GMT (UTC+0).
    In July, London is BST (UTC+1).
    """
    # Winter test (January - UTC+0)
    jan_str = "2026-01-15T09:30:00Z"
    dt_jan = parse_iso_utc(jan_str)
    assert dt_jan.tzinfo == timezone.utc
    assert to_london_display(dt_jan) == "2026-01-15 09:30 GMT"

    # Summer test (July - UTC+1 / BST)
    jul_str = "2026-07-15T09:30:00Z"
    dt_jul = parse_iso_utc(jul_str)
    # 09:30 UTC is 10:30 BST
    assert to_london_display(dt_jul) == "2026-07-15 10:30 BST"


def test_cutoff_datetime_computation():
    """
    Test cutoff time construction in London and conversion to UTC.
    """
    # Decision date: 2026-01-10, cutoff: 09:30 London
    cutoff_utc = compute_cutoff_datetime_utc(date(2026, 1, 10), "09:30")
    # In January, 09:30 GMT is 09:30 UTC
    assert cutoff_utc == datetime(2026, 1, 10, 9, 30, tzinfo=timezone.utc)
    assert format_iso_utc(cutoff_utc) == "2026-01-10T09:30:00Z"

    # In summer (e.g. 2026-06-10), 09:30 BST is 08:30 UTC
    summer_cutoff_utc = compute_cutoff_datetime_utc(date(2026, 6, 10), "09:30")
    assert summer_cutoff_utc == datetime(2026, 6, 10, 8, 30, tzinfo=timezone.utc)


def test_daylight_saving_transitions():
    """
    Test 9: Daylight-saving transitions are handled safely.
    - Standard day: 48 settlement periods.
    - Spring transition (clocks forward 1 hour): 46 settlement periods (23 hours).
    - Autumn transition (clocks back 1 hour): 50 settlement periods (25 hours).
    """
    # 1. Standard day in January 2026
    jan_periods = get_expected_settlement_periods_for_date(date(2026, 1, 15))
    assert len(jan_periods) == 48
    assert jan_periods[0][0] == 1  # period 1
    assert jan_periods[-1][0] == 48  # period 48

    # 2. UK Spring clock change in 2026: Sunday, 29 March 2026
    spring_periods = get_expected_settlement_periods_for_date(date(2026, 3, 29))
    assert len(spring_periods) == 46, f"Expected 46 periods on spring clock change, got {len(spring_periods)}"

    # 3. UK Autumn clock change in 2026: Sunday, 25 October 2026
    autumn_periods = get_expected_settlement_periods_for_date(date(2026, 10, 25))
    assert len(autumn_periods) == 50, f"Expected 50 periods on autumn clock change, got {len(autumn_periods)}"


def test_settlement_period_determination():
    """
    Verify settlement period calculation from datetime.
    """
    # 00:00:00 London is Settlement Period 1
    dt1 = datetime(2026, 1, 10, 0, 0, tzinfo=timezone.utc)
    d1, p1 = get_settlement_period_from_datetime(dt1)
    assert p1 == 1

    # 00:30:00 London is Settlement Period 2
    dt2 = datetime(2026, 1, 10, 0, 30, tzinfo=timezone.utc)
    d2, p2 = get_settlement_period_from_datetime(dt2)
    assert p2 == 2

    # 23:30:00 London is Settlement Period 48
    dt48 = datetime(2026, 1, 10, 23, 30, tzinfo=timezone.utc)
    d48, p48 = get_settlement_period_from_datetime(dt48)
    assert p48 == 48
