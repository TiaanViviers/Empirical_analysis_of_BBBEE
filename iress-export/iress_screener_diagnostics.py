#!/usr/bin/env python3
"""Audit saved IRESS Screener page snapshots against the CSV and thesis master."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path

import pyarrow.parquet as pq

from iress_screener_metadata import decode_instrument_id


def audit(pages_dir: Path, csv_path: Path, summary_path: Path, master_path: Path) -> dict:
    files = sorted(pages_dir.glob("page_*.json"))
    pages = [json.loads(path.read_text(encoding="utf-8")) for path in files]
    page_ids = {p["page"]: [r["instrument_id"] for r in p["rows"]] for p in pages}
    all_rows = [r for p in pages for r in p["rows"]]
    ids = [r["instrument_id"] for r in all_rows]
    duplicates = sorted(key for key, count in Counter(ids).items() if count > 1)
    overlaps = []
    for i, left in enumerate(pages):
        for right in pages[i + 1:]:
            shared = sorted(set(page_ids[left["page"]]) & set(page_ids[right["page"]]))
            if shared:
                same_content = [
                    {k: v for k, v in row.items() if k not in ("position", "captured_at")}
                    for row in left["rows"]
                ] == [
                    {k: v for k, v in row.items() if k not in ("position", "captured_at")}
                    for row in right["rows"]
                ]
                overlaps.append({"page_a": left["page"], "page_b": right["page"],
                                 "shared_count": len(shared), "shared_ids": shared,
                                 "identical_content": same_content})
    decode_errors = []
    for p in pages:
        for row in p["rows"]:
            try:
                decoded = decode_instrument_id(row["landing_href"])
                if decoded != row["instrument_id"]:
                    decode_errors.append({"page": p["page"], "id": row["instrument_id"],
                                          "decoded": decoded})
            except Exception as exc:
                decode_errors.append({"page": p["page"], "id": row["instrument_id"],
                                      "error": str(exc)})
    page_report = []
    for p in pages:
        own = page_ids[p["page"]]
        other = set().union(*(set(v) for k, v in page_ids.items() if k != p["page"]))
        page_report.append({
            "page": p["page"], "first": p["first"], "last": p["last"],
            "total": p["total"], "row_count": len(own), "unique_ids": len(set(own)),
            "overlap_count": len(set(own) & other),
            "first_five_ids": own[:5], "last_five_ids": own[-5:],
            "first_company_name": p["rows"][0]["company_name"] if own else None,
            "last_company_name": p["rows"][-1]["company_name"] if own else None,
        })
    with csv_path.open(newline="", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    master_rows = pq.read_table(master_path, columns=["instrument_id", "company_name"]).to_pylist()
    master_ids = {row["instrument_id"] for row in master_rows}
    screener_ids = set(ids)
    thesis_only = sorted(master_ids - screener_ids)
    screener_only = sorted(screener_ids - master_ids)
    gaps = []
    for left, right in zip(pages, pages[1:]):
        if not left["rows"] or not right["rows"]:
            continue
        tail = left["rows"][-1]["company_name"].casefold()
        head = right["rows"][0]["company_name"].casefold()
        missing_between = [r["instrument_id"] for r in master_rows
                           if r["instrument_id"] in thesis_only
                           and tail < r["company_name"].casefold() < head]
        if missing_between:
            gaps.append({"after_page": left["page"], "before_page": right["page"],
                         "master_ids_between": sorted(missing_between),
                         "count": len(missing_between),
                         "boundary_names": [left["rows"][-1]["company_name"],
                                            right["rows"][0]["company_name"]]})
    repeated_pairs = [x for x in overlaps if x["identical_content"]]
    if repeated_pairs and gaps:
        pair = repeated_pairs[0]
        gap = gaps[0]
        root_cause = (
            f"Page {pair['page_b']} records the same instruments as page "
            f"{pair['page_a']} despite a different reported pagination range. "
            f"{gap['count']} missing thesis IDs lie in the alphabetical gap "
            f"between pages {gap['after_page']} and {gap['before_page']}. "
            "This supports an asynchronous pagination/content race; the saved files "
            "cannot establish the exact browser event timing."
        )
    elif not overlaps and not gaps and not decode_errors:
        root_cause = "No repeated page content, master coverage gap, or ID decode error detected."
    else:
        root_cause = (
            "Inspect page overlaps, ordering gaps, and decoded IDs; saved output does not "
            "establish one definitive cause."
        )
    return {
        "total_saved_pages": len(pages), "total_captured_rows": len(ids),
        "unique_instrument_ids": len(screener_ids), "duplicate_instrument_ids": duplicates,
        "pages": page_report, "overlapping_pages": overlaps,
        "base64_decode_errors": decode_errors,
        "csv_validation": {"rows": len(csv_rows),
                           "ids_match_pages": [r["instrument_id"] for r in csv_rows] == ids,
                           "positions_match_pages": all(int(c["position"]) == p["position"]
                                                        for c, p in zip(csv_rows, all_rows))
                           and len(csv_rows) == len(all_rows)},
        "summary_validation": {
            "rows_match": summary.get("rows") == len(ids),
            "unique_ids_match": summary.get("unique_instrument_ids") == len(screener_ids),
            "duplicates_match": summary.get("duplicate_instrument_ids") == duplicates,
        },
        "master_reconciliation": {"master_unique_ids": len(master_ids),
                                  "matched_ids": len(master_ids & screener_ids),
                                  "in_master_not_screener": thesis_only,
                                  "in_screener_not_master": screener_only},
        "alphabetical_master_gaps": gaps,
        "root_cause": root_cause,
        "recommended_fix": "Wait for both the expected footer and changed, non-overlapping "
                           "instrument content; verify total, row count, filters and "
                           "ordering before saving each page. Stage new output until "
                           "the complete run validates.",
    }


def print_report(report: dict) -> None:
    print("=== IRESS SCREENER EXTRACTION DIAGNOSTICS ===")
    print(f"Total saved page files: {report['total_saved_pages']}")
    print(f"Total captured rows: {report['total_captured_rows']}")
    print(f"Unique instrument IDs: {report['unique_instrument_ids']}")
    print(f"Duplicate instrument IDs: {len(report['duplicate_instrument_ids'])}")
    print("\nPAGE ANALYSIS")
    for p in report["pages"]:
        print(f"Page {p['page']:02d}: {p['row_count']} rows, {p['unique_ids']} unique, "
              f"range {p['first']}-{p['last']} of {p['total']}, "
              f"overlap {p['overlap_count']}")
        print("  First: " + ", ".join(p["first_five_ids"]))
        print("  Last:  " + ", ".join(p["last_five_ids"]))
    print("\nDUPLICATE PAGE ANALYSIS")
    if not report["overlapping_pages"]:
        print("No overlapping pages")
    for pair in report["overlapping_pages"]:
        print(f"Page {pair['page_a']:02d} overlaps Page {pair['page_b']:02d}: "
              f"{pair['shared_count']} shared IDs; identical content: {pair['identical_content']}")
    print("Base64 decode mismatches: " + str(len(report["base64_decode_errors"])))
    print("CSV ID sequence matches pages: " + str(report["csv_validation"]["ids_match_pages"]))
    print("\nMISSING COVERAGE")
    m = report["master_reconciliation"]
    print(f"Thesis master IDs absent from Screener: {len(m['in_master_not_screener'])}")
    print(f"Screener IDs absent from thesis master: {len(m['in_screener_not_master'])}")
    for gap in report["alphabetical_master_gaps"]:
        print(f"Between pages {gap['after_page']:02d} and {gap['before_page']:02d}: "
              f"{gap['count']} thesis IDs between {gap['boundary_names'][0]!r} "
              f"and {gap['boundary_names'][1]!r}")
    print("\nROOT CAUSE\n" + report["root_cause"])
    print("\nRECOMMENDED FIX\n" + report["recommended_fix"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", type=Path, default=Path("metadata/screener_pages"))
    parser.add_argument("--csv", type=Path, default=Path("metadata/jse_screener_snapshot.csv"))
    parser.add_argument("--summary", type=Path, default=Path("metadata/jse_screener_snapshot.summary.json"))
    parser.add_argument("--master", type=Path, default=Path("dist/thesis_data/data/instruments.parquet"))
    parser.add_argument("--out", type=Path, default=Path("metadata/screener_diagnostics.json"))
    args = parser.parse_args()
    report = audit(args.pages, args.csv, args.summary, args.master)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print_report(report)
    print("\nSaved diagnostics: " + str(args.out.resolve()))


if __name__ == "__main__":
    main()
