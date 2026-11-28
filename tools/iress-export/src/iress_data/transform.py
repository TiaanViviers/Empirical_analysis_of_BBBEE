"""Per-row financial diagnostics using only information at or before the row."""

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date
from typing import Any

from .config import Config
from .schemas import QUALITY_RULE_VERSION
from .validation import adjacent_return, finite, valid_price

TICKER = re.compile(r"([^:\s]+):XJSE:EQU\Z")


def ticker_from_identifier(identifier: str) -> str | None:
    match = TICKER.fullmatch(identifier)
    return match[1] if match else None


def as_int64(value: float | int | None) -> int | None:
    if value is None:
        return None
    if not finite(value):
        raise ValueError(f"Non-finite quantity cannot be preserved as Int64: {value!r}")
    result = int(value)
    if result != value or not -(2**63) <= result < 2**63:
        raise ValueError(f"Quantity cannot be preserved as Int64 without rounding: {value!r}")
    return result


@dataclass
class TrailingState:
    instrument_id: str | None = None
    previous_close: float | None = None
    previous_date: date | None = None
    previous_position: int | None = None
    previous_price_date: date | None = None
    previous_price_position: int | None = None
    constant_sessions: int = 0


def transform_records(records: Iterable[dict[str, Any]], calendar: list[date],
                      cfg: Config) -> Iterator[dict[str, Any]]:
    """Input must be unique and ordered by instrument_id,date; state is bounded."""
    positions = {d:i for i,d in enumerate(calendar)}
    state = TrailingState()
    for row in records:
        ident = row["instrument_id"]
        if ident != state.instrument_id:
            state = TrailingState(instrument_id=ident)
        d, price = row["date"], row["close_raw"]
        position = positions[d]
        if state.previous_date is not None and d <= state.previous_date:
            raise ValueError(f"Non-unique or unsorted canonical observations: {ident} {d}")
        volume, trades = as_int64(row["volume"]), as_int64(row["number_of_trades"])
        valid = valid_price(price)
        adjacent = state.previous_position is not None and position == state.previous_position+1
        pair_valid = adjacent and valid and valid_price(state.previous_close)
        change = adjacent_return(state.previous_close, price, state.previous_position, position)
        unchanged = price == state.previous_close if pair_valid else None
        trailing = state.constant_sessions+1 if unchanged else 1 if valid else 0
        positive_volume = volume is not None and volume > 0
        issues = row["parse_issues"]
        result = {
            "date": d, "instrument_id": ident, "ticker": ticker_from_identifier(ident),
            "company_name": row["company_name"], "close_raw": price,
            "volume": volume, "number_of_trades": trades,
            **{name:row[name] for name in ("source_batch","source_file","source_sheet","source_row",
                                          "source_sha256","duplicate_copy_count")},
            "has_valid_price": valid, "is_missing_price": price is None,
            "is_zero_price": price == 0, "is_negative_price": finite(price) and price < 0,
            "is_nonfinite_price": price is not None and not finite(price),
            "invalid_price": (price is not None and not valid) or "close_raw:" in issues,
            "has_positive_volume": positive_volume, "is_zero_volume": volume == 0,
            "is_missing_volume": volume is None,
            "is_negative_volume": volume is not None and volume < 0,
            "is_missing_trade_count": trades is None,
            "is_negative_trade_count": trades is not None and trades < 0,
            "is_empty_placeholder": price is None and volume is None and trades is None and not issues,
            "numeric_parse_issue": bool(issues), "parse_issues": issues,
            "unparsed_values": row["unparsed_values"],
            "previous_observed_date": state.previous_date,
            "previous_price_date": state.previous_price_date,
            "price_gap_sessions": None if state.previous_price_position is None else position-state.previous_price_position,
            "is_adjacent_to_previous_session": adjacent,
            "has_valid_adjacent_price": pair_valid,
            "missing_or_invalid_adjacent_observation": not pair_valid,
            "unchanged_adjacent_price": unchanged, "trailing_constant_price_sessions": trailing,
            "potential_stale_price": valid and not positive_volume and (unchanged is True or trailing >= cfg.stale_run),
            "extreme_price_change": None if change is None else abs(change) > cfg.extreme_threshold,
            "diagnostic_price_return": change, "quality_rule_version": QUALITY_RULE_VERSION,
        }
        state.previous_close, state.previous_date, state.previous_position = price, d, position
        state.constant_sessions = trailing
        if valid:
            state.previous_price_date, state.previous_price_position = d, position
        yield result
