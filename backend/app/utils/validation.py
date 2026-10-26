from datetime import date
from typing import Tuple
from fastapi import HTTPException


def parse_and_validate_date(date_str: str, param_name: str = "date") -> date:
    try:
        parts = [int(p) for p in date_str.strip().split("-")]
        if len(parts) != 3:
            raise ValueError
        return date(parts[0], parts[1], parts[2])
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {param_name} format '{date_str}'. Expected YYYY-MM-DD (e.g. 2026-01-10).",
        )


def parse_and_validate_cutoff(cutoff_str: str) -> str:
    cleaned = cutoff_str.strip()
    parts = cleaned.split(":")
    if len(parts) != 2:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid cutoff_time '{cutoff_str}'. Expected HH:MM in 24-hour format (e.g. 09:30).",
        )
    try:
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
        return f"{hour:02d}:{minute:02d}"
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"Cutoff time '{cutoff_str}' out of range. Hours must be 0-23 and minutes 0-59.",
        )


def validate_date_range(start_date: date, end_date: date) -> None:
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail=f"start_date ({start_date.isoformat()}) must be earlier than or equal to end_date ({end_date.isoformat()}).",
        )
    # Check max range limit to prevent accidental huge queries (e.g. max 62 days)
    delta = (end_date - start_date).days
    if delta > 62:
        raise HTTPException(
            status_code=400,
            detail="Requested date range exceeds maximum allowed window of 62 days.",
        )
