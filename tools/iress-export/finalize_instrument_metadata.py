#!/usr/bin/env python3
"""Build the dated Screener metadata Parquet and extend the thesis handover package."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from iress_data.instrument_metadata import FILENAME, augment_handover, process_metadata


def main() -> None:
    root = Path(__file__).resolve().parent
    output = root / "data/processed" / FILENAME
    metrics = process_metadata(
        root / "metadata/jse_screener_snapshot.csv",
        root / "metadata/jse_screener_snapshot.summary.json",
        root / "data/processed/instruments.parquet",
        output,
    )
    print(f"Processed metadata: {output}")
    print(f"Records: {metrics['rows']}; valid ISINs: {metrics['valid_isins']}; "
          f"historical matches: {metrics['historical_master_matches']}")
    augment_handover(root / "dist/thesis_data", output, metrics)
    print(f"Verified handover: {root / 'dist/thesis_data'}")


if __name__ == "__main__":
    main()
