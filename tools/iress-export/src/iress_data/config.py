"""Explicit audit assumptions; none of these are sample eligibility rules."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

EVENTS = (
    ("mining_charter_2017", "Mining Charter 2017", date(2017, 6, 15)),
    ("mining_charter_2018", "Final Mining Charter 2018", date(2018, 9, 27)),
    ("ee_draft_2023", "Draft EE sector targets", date(2023, 5, 12)),
    ("ee_final_2025", "Final EE sector targets", date(2025, 4, 15)),
    ("bbbee_draft_2026", "Draft B-BBEE Code amendments", date(2026, 1, 29)),
)
START = date(2016, 1, 1)
END = date(2026, 3, 31)


@dataclass(frozen=True)
class Config:
    root: Path
    exports: Path
    intermediate: Path
    reports: Path
    expected_batches: int = 19
    chunk_rows: int = 20_000
    memory_limit: str = "512MB"
    stale_run: int = 20
    extreme_threshold: float = 0.30

    @classmethod
    def from_root(cls, root: Path) -> "Config":
        root = root.resolve()
        return cls(root, root / "exports", root / "data/intermediate", root / "reports")
