"""Regression checks for Screener pagination and saved metadata audits."""

from __future__ import annotations

import base64
import csv
import json
from pathlib import Path
import tempfile
import unittest

import pyarrow as pa
import pyarrow.parquet as pq

from iress_screener_metadata import (
    decode_instrument_id, parse_footer, promote_run, save_page_snapshot,
    validate_page_records, wait_for_page_snapshot,
)
from iress_screener_diagnostics import audit


def record(identifier: str, name: str, position: int) -> dict:
    href = "#/InstrumentLanding/" + base64.b64encode(identifier.encode()).decode()
    return {"instrument_id": identifier, "landing_href": href,
            "company_name": name, "position": position,
            "instrument_type": "Equities and Companies",
            "exchange": "Jse Securities Exchange", "listing_status": "Listed"}


class FakePage:
    def __init__(self, snapshots):
        self.snapshots = iter(snapshots)
        self.latest = None
        self.wait_calls = []

    def wait_for_function(self, expression, *, arg, timeout):
        self.wait_calls.append(arg)
        self.latest = next(self.snapshots)

    def evaluate(self, expression):
        return self.latest


class ScreenerTests(unittest.TestCase):
    def test_footer_with_commas(self):
        self.assertEqual(parse_footer("Displaying Results 901 - 1,000 of 1,872"),
                         (901, 1000, 1872))
        self.assertEqual(parse_footer("Displaying Results 1,801 - 1,872 of 1,872"),
                         (1801, 1872, 1872))

    def test_base64_decoding(self):
        href = record("ABC.DEL:XJSE:EQU", "Example", 1)["landing_href"]
        self.assertEqual(decode_instrument_id(href), "ABC.DEL:XJSE:EQU")
        self.assertEqual(decode_instrument_id(href.rstrip("=") + "?x=1"),
                         "ABC.DEL:XJSE:EQU")
        with self.assertRaises(ValueError):
            decode_instrument_id("#/InstrumentLanding/bad!!")

    def test_stale_page_is_not_accepted(self):
        old = record("OLD:XJSE:EQU", "Old", 1)
        new = record("NEW:XJSE:EQU", "New", 2)
        page = FakePage([
            {"text": "Displaying Results 2 - 2 of 2", "rows": [old]},
            {"text": "Displaying Results 2 - 2 of 2", "rows": [new]},
        ])
        result = wait_for_page_snapshot(page, 2, seen_hrefs={old["landing_href"]},
                                        timeout_ms=1000)
        self.assertEqual(result[3][0]["landing_href"], new["landing_href"])
        self.assertEqual(len(page.wait_calls), 2)

    def test_repeated_and_out_of_order_pages_fail(self):
        prior = [record("A:XJSE:EQU", "Alpha", 1)]
        with self.assertRaisesRegex(RuntimeError, "repeats"):
            validate_page_records([record("A:XJSE:EQU", "Alpha", 2)], 2, 2, prior)
        with self.assertRaisesRegex(RuntimeError, "order moved backward"):
            validate_page_records([record("B:XJSE:EQU", "Aardvark", 2)], 2, 2, prior)
        with self.assertRaisesRegex(RuntimeError, "filters changed"):
            bad = record("B:XJSE:EQU", "Beta", 2)
            bad["exchange"] = "Other"
            validate_page_records([bad], 2, 2, prior)

    def test_saved_page_is_immutable_on_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page_01.json"
            payload = {"page": 1, "rows": [record("A:XJSE:EQU", "Alpha", 1)]}
            self.assertTrue(save_page_snapshot(path, payload))
            self.assertFalse(save_page_snapshot(path, payload))
            changed = {"page": 1, "rows": [record("B:XJSE:EQU", "Beta", 1)]}
            with self.assertRaisesRegex(RuntimeError, "differs"):
                save_page_snapshot(path, changed)
            self.assertEqual(json.loads(path.read_text()), payload)

    def test_promotion_archives_previous_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_pages = root / "screener_pages"
            old_pages.mkdir()
            (old_pages / "page_01.json").write_text("old")
            out = root / "snapshot.csv"
            out.write_text("old csv")
            summary = root / "snapshot.summary.json"
            summary.write_text("old summary")
            run = root / "run_1"
            pages = run / "pages"
            pages.mkdir(parents=True)
            (pages / "page_01.json").write_text("new")
            (run / out.name).write_text("new csv")
            (run / summary.name).write_text("new summary")
            promote_run(run, out, pages)
            self.assertEqual((old_pages / "page_01.json").read_text(), "new")
            self.assertEqual((run / "previous_canonical/screener_pages/page_01.json").read_text(), "old")
            self.assertEqual(out.read_text(), "new csv")
            self.assertEqual((run / "previous_canonical/snapshot.csv").read_text(), "old csv")

    def test_audit_detects_duplicate_page_and_missing_master_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pages = root / "pages"
            pages.mkdir()
            left = record("A:XJSE:EQU", "Alpha", 1)
            right = record("A:XJSE:EQU", "Alpha", 2)
            for number, row in ((1, left), (2, right)):
                (pages / f"page_{number:02d}.json").write_text(json.dumps({
                    "page": number, "first": number, "last": number,
                    "total": 2, "rows": [row],
                }))
            csv_path = root / "snapshot.csv"
            with csv_path.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["position", "instrument_id"])
                writer.writeheader()
                writer.writerows({"position": row["position"],
                                  "instrument_id": row["instrument_id"]}
                                 for row in (left, right))
            summary_path = root / "snapshot.summary.json"
            summary_path.write_text(json.dumps({
                "rows": 2, "unique_instrument_ids": 1,
                "duplicate_instrument_ids": ["A:XJSE:EQU"],
            }))
            master_path = root / "master.parquet"
            pq.write_table(pa.table({"instrument_id": ["A:XJSE:EQU", "B:XJSE:EQU"],
                                     "company_name": ["Alpha", "Beta"]}), master_path)
            report = audit(pages, csv_path, summary_path, master_path)
            self.assertEqual(report["total_saved_pages"], 2)
            self.assertEqual(report["total_captured_rows"], 2)
            self.assertEqual(report["unique_instrument_ids"], 1)
            self.assertEqual(report["overlapping_pages"][0]["shared_count"], 1)
            self.assertTrue(report["overlapping_pages"][0]["identical_content"])
            self.assertEqual(report["master_reconciliation"]["in_master_not_screener"],
                             ["B:XJSE:EQU"])
            self.assertEqual(report["base64_decode_errors"], [])


if __name__ == "__main__":
    unittest.main()
