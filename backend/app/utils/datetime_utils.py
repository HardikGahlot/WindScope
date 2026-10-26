from datetime import date, datetime, time, timedelta, timezone
from typing import List, Tuple
from zoneinfo import ZoneInfo

LONDON_TZ = ZoneInfo("Europe/London")
UTC_TZ = timezone.utc


def parse_iso_utc(timestamp_str: str) -> datetime:
    """
    Parse an ISO-8601 timestamp string into a timezone-aware UTC datetime.
    Handles 'Z' suffix and explicit offset notations.
    """
    if not timestamp_str:
        raise ValueError("Empty timestamp string")
    
    clean_str = timestamp_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(clean_str)
    if dt.tzinfo is None:
        # If naive, assume UTC as per Elexon BMRS convention
        dt = dt.replace(tzinfo=UTC_TZ)
    return dt.astimezone(UTC_TZ)


def format_iso_utc(dt: datetime) -> str:
    """Format timezone-aware datetime to ISO-8601 UTC string ending in 'Z'."""
    utc_dt = dt.astimezone(UTC_TZ)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def to_london_display(dt: datetime) -> str:
    """Format datetime for Europe/London display with explicit timezone label."""
    london_dt = dt.astimezone(LONDON_TZ)
    tz_label = london_dt.strftime("%Z")
    return london_dt.strftime(f"%Y-%m-%d %H:%M {tz_label}")


def compute_cutoff_datetime_utc(decision_date: date, cutoff_time_str: str) -> datetime:
    """
    Given a decision date (e.g. 2026-01-01) and a cutoff time string (e.g. '09:30'),
    construct the Europe/London localized datetime and convert to UTC.
    Inclusive boundary: records with publishTime <= cutoff_datetime_utc are eligible.
    """
    parts = cutoff_time_str.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid cutoff time format '{cutoff_time_str}', expected 'HH:MM'")
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Cutoff time values out of range: {cutoff_time_str}")
    
    local_time = time(hour=hour, minute=minute, second=0)
    # Combine with date in Europe/London timezone
    # Using fold=0 ensures standard time resolution in ambiguous autumn transition
    local_dt = datetime.combine(decision_date, local_time, tzinfo=LONDON_TZ)
    return local_dt.astimezone(UTC_TZ)


def get_expected_settlement_periods_for_date(delivery_date: date) -> List[Tuple[int, datetime, datetime]]:
    """
    Generate all expected half-hour settlement periods for a UK delivery date in Europe/London.
    Returns list of tuples: (settlement_period_num, start_time_utc, start_time_london).
    Handles standard 48-period days, 46-period clock change (spring), and 50-period clock change (autumn).
    """
    # Start at 00:00:00 London time on delivery_date
    current_london = datetime.combine(delivery_date, time(0, 0), tzinfo=LONDON_TZ)
    next_day_london = datetime.combine(delivery_date + timedelta(days=1), time(0, 0), tzinfo=LONDON_TZ)
    
    periods = []
    period_idx = 1
    
    # Step half-hourly in UTC
    current_utc = current_london.astimezone(UTC_TZ)
    end_utc = next_day_london.astimezone(UTC_TZ)
    
    while current_utc < end_utc:
        london_repr = current_utc.astimezone(LONDON_TZ)
        periods.append((period_idx, current_utc, london_repr))
        period_idx += 1
        current_utc += timedelta(minutes=30)
        
    return periods


def get_settlement_period_from_datetime(dt: datetime) -> Tuple[date, int]:
    """
    Given a delivery timestamp, determine the UK Settlement Date and Settlement Period (1-48+).
    Settlement Period 1 starts at 00:00:00 London time.
    """
    london_dt = dt.astimezone(LONDON_TZ)
    settlement_date = london_dt.date()
    # Calculate minutes from start of London day
    day_start = datetime.combine(settlement_date, time(0, 0), tzinfo=LONDON_TZ)
    diff_minutes = (london_dt - day_start).total_seconds() / 60.0
    period = int(diff_minutes // 30) + 1
    return settlement_date, period
