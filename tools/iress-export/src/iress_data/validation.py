"""Small reusable numerical and calendar diagnostics."""

import math
from datetime import date
from typing import Any


def valid_price(value: Any) -> bool:
    return value is not None and math.isfinite(value) and value > 0


def finite(value: Any) -> bool:
    return value is not None and math.isfinite(value)


def longest_run(flags: list[bool]) -> int:
    longest = current = 0
    for flag in flags:
        current = current + 1 if flag else 0
        longest = max(longest, current)
    return longest


def adjacent_return(previous: float | None, current: float | None,
                    previous_position: int | None, position: int) -> float | None:
    """A gap or nonpositive/nonfinite close breaks one-session returns."""
    if (previous_position is None or position != previous_position + 1
            or not valid_price(previous) or not valid_price(current)):
        return None
    result = current / previous - 1
    return result if math.isfinite(result) else None


def calendar_summary(dates: list[date]) -> dict[str, Any]:
    dates = sorted(set(dates))
    gaps = [(b - a).days for a, b in zip(dates, dates[1:])]
    months = {(d.year, d.month) for d in dates}
    month_end = sum(date.fromordinal(d.toordinal() + 1).month != d.month for d in dates)
    monthly = len(dates) >= 3 and len(months) == len(dates) and all(g >= 20 for g in gaps)
    daily = len(dates) >= 3 and sum(g == 1 for g in gaps) / len(gaps) > .5
    return {
        "start": dates[0].isoformat() if dates else None,
        "end": dates[-1].isoformat() if dates else None,
        "unique_dates": len(dates), "weekend_dates": sum(d.weekday() > 4 for d in dates),
        "calendar_month_ends": month_end,
        "frequency": "monthly" if monthly else "daily_like" if daily else "irregular",
        "gap_days": {str(g): gaps.count(g) for g in sorted(set(gaps))},
    }
