#!/usr/bin/env python3
"""Export the visible IRESS Expert Screener table through an authenticated local browser.

Uses only the user-visible Screener UI and DOM. No private endpoints or credentials.
Run only where local/institutional terms permit automated access.
"""

from __future__ import annotations

import argparse
import base64
import csv
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
from collections import Counter

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

EXPERT_URL = "https://expert-iress-co-za.ez.sun.ac.za/"
ROW_SELECTOR = 'tr:has(a[href^="#/InstrumentLanding/"])'
FOOTER_PATTERN = re.compile(
    r"Displaying\s+Results\s+([\d,]+)\s*[-–]\s*([\d,]+)\s+of\s+([\d,]+)", re.I
)
FIELDS = [
    "captured_at", "position", "instrument_id", "company_name", "ticker", "isin",
    "isin_format_valid", "instrument_type", "exchange", "country", "listing_status",
    "landing_href",
]
JS_ROWS = r"""rows => rows.map(tr => {
  const td = Array.from(tr.querySelectorAll('td'));
  const a = td[1]?.querySelector('a[href^="#/InstrumentLanding/"]');
  return {
    company_name: td[1]?.innerText.trim() ?? '',
    ticker: td[2]?.innerText.trim() ?? '',
    isin: td[3]?.innerText.trim() ?? '',
    instrument_type: td[4]?.innerText.trim() ?? '',
    exchange: td[5]?.innerText.trim() ?? '',
    country: td[6]?.innerText.trim() ?? '',
    listing_status: td[7]?.innerText.trim() ?? '',
    landing_href: a?.getAttribute('href') ?? '',
    td_count: td.length
  };
})"""
READY_PAGE_JS = r"""({start, seen}) => {
  const match = document.body.innerText.match(
    /Displaying\s+Results\s+([\d,]+)\s*[-–]\s*([\d,]+)\s+of\s+([\d,]+)/i
  );
  if (!match) return false;
  const first = Number(match[1].replaceAll(',', ''));
  const last = Number(match[2].replaceAll(',', ''));
  const total = Number(match[3].replaceAll(',', ''));
  if (first !== start || last !== Math.min(start + 99, total)) return false;
  const links = Array.from(document.querySelectorAll(
    'tr a[href^="#/InstrumentLanding/"]'
  ));
  const hrefs = links.map(link => link.getAttribute('href'));
  const previous = new Set(seen);
  return hrefs.length === last - first + 1 &&
    new Set(hrefs).size === hrefs.length &&
    hrefs.every(href => !previous.has(href));
}"""
SNAPSHOT_JS = """() => ({
  text: document.body.innerText,
  rows: (""" + JS_ROWS + """)(Array.from(
    document.querySelectorAll('tr:has(a[href^="#/InstrumentLanding/"])')
  ))
})"""


def decode_instrument_id(href: str) -> str:
    prefix = "#/InstrumentLanding/"
    if not href.startswith(prefix):
        raise ValueError(f"Unexpected instrument href: {href!r}")
    payload = href[len(prefix):].split("?", 1)[0]
    payload += "=" * (-len(payload) % 4)
    decoded = base64.b64decode(payload, validate=True).decode("utf-8")
    if ":" not in decoded or not decoded.strip():
        raise ValueError(f"Unexpected decoded instrument ID: {decoded!r}")
    return decoded


def parse_footer(text: str):
    match = FOOTER_PATTERN.search(text)
    if not match:
        raise RuntimeError("Could not find 'Displaying Results START - END of TOTAL' footer. Check Screener.")
    return tuple(int(value.replace(",", "")) for value in match.groups())


def wait_for_page_snapshot(page, start: int, seen_hrefs=(), timeout_ms: int = 45000):
    """Accept only a complete page whose instruments were not captured earlier."""
    deadline = time.monotonic() + timeout_ms / 1000
    last_seen = None
    while time.monotonic() < deadline:
        remaining_ms = max(1, int((deadline - time.monotonic()) * 1000))
        try:
            page.wait_for_function(READY_PAGE_JS, arg={"start": start, "seen": list(seen_hrefs)},
                                   timeout=remaining_ms)
        except PlaywrightTimeoutError:
            snapshot = page.evaluate(SNAPSHOT_JS)
            match = FOOTER_PATTERN.search(snapshot["text"])
            footer = parse_footer(snapshot["text"]) if match else None
            hrefs = [row["landing_href"] for row in snapshot["rows"]]
            overlap = sorted(set(hrefs) & set(seen_hrefs))
            raise RuntimeError(
                f"Screener page starting at {start} did not show new complete content "
                f"within {timeout_ms / 1000:g}s; footer={footer}, rows={len(hrefs)}, "
                f"previously captured IDs={len(overlap)}. "
                "The results counter may have advanced before the table updated."
            ) from None
        snapshot = page.evaluate(SNAPSHOT_JS)
        match = FOOTER_PATTERN.search(snapshot["text"])
        if match:
            first, last, total = parse_footer(snapshot["text"])
            hrefs = [row["landing_href"] for row in snapshot["rows"]]
            last_seen = (first, last, total, len(hrefs))
            if (first == start and last == min(start + 99, total)
                    and len(hrefs) == last - first + 1
                    and len(set(hrefs)) == len(hrefs)
                    and not set(hrefs).intersection(seen_hrefs)):
                return first, last, total, snapshot["rows"]
        else:
            last_seen = ("footer absent", len(snapshot["rows"]))
    raise RuntimeError(
        f"Screener page starting at {start} did not finish loading; last state: {last_seen}"
    )


def ensure_100_results(page):
    """Set Screener page size using the page-size control recorded with Codegen."""
    page.locator(ROW_SELECTOR).first.wait_for(state="attached", timeout=45000)
    count = page.locator(ROW_SELECTOR).count()
    if count == 100:
        print("  Screener already shows 100 rows.")
        return
    print(f"  Screener currently shows {count} rows; setting Show 100 Results...")
    page.locator("dt > .icon").click(timeout=15000)
    page.get_by_text("100", exact=True).last.click(timeout=15000)
    page.wait_for_function(
        "document.querySelectorAll('tr a[href^=\"#/InstrumentLanding/\"]').length === 100",
        timeout=45000,
    )
    print("  Screener now shows 100 rows.")


def debug_layout(page):
    """Collect browser layout diagnostics if IRESS pagination is missing."""
    try:
        return page.evaluate("""() => ({
          viewport: { width: innerWidth, height: innerHeight },
          documentHeight: document.documentElement.scrollHeight,
          rowCount: document.querySelectorAll('tr a[href^="#/InstrumentLanding/"]').length,
          footerFoundInText: /Displaying\\s+Results/i.test(document.body.innerText),
          bodyTextTail: document.body.innerText.slice(-500)
        })""")
    except Exception as exc:
        return {"diagnostic_error": str(exc)}


def save_csv(path: Path, records: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)


def validate_page_records(page_rows: list[dict], first: int, last: int,
                          earlier_rows: list[dict]) -> None:
    if len(page_rows) != last - first + 1:
        raise RuntimeError(f"Page {first}-{last} has {len(page_rows)} rows")
    ids = [r["instrument_id"] for r in page_rows]
    repeated = sorted(key for key, count in Counter(ids).items() if count > 1)
    overlap = sorted(set(ids) & {r["instrument_id"] for r in earlier_rows})
    if repeated or overlap:
        raise RuntimeError(
            f"Page {first}-{last} repeats {len(repeated)} IDs within the page and "
            f"{len(overlap)} IDs from earlier pages. Examples: {(repeated + overlap)[:8]}"
        )
    for row in page_rows:
        if (row["instrument_type"] != "Equities and Companies"
                or row["exchange"] != "Jse Securities Exchange"
                or row["listing_status"] not in ("Listed", "Delisted")):
            raise RuntimeError(f"Screener filters changed at result {row['position']}: {row!r}")
    if earlier_rows and (page_rows[0]["company_name"].casefold()
                         < earlier_rows[-1]["company_name"].casefold()):
        raise RuntimeError(
            f"Screener Name order moved backward between "
            f"{earlier_rows[-1]['company_name']!r} and "
            f"{page_rows[0]['company_name']!r}; check sorting or pagination."
        )


def save_page_snapshot(path: Path, payload: dict) -> bool:
    """Never replace an existing staged page with different content."""
    if path.exists():
        prior = json.loads(path.read_text(encoding="utf-8"))
        if prior != payload:
            raise RuntimeError(
                f"Saved {path} differs from the live page. "
                "Check filters, sorting, or changed Screener data before resuming."
            )
        return False
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return True


def promote_run(run_dir: Path, out: Path, pages_dir: Path) -> None:
    """Keep the previous canonical output as an archive until the run validates."""
    canonical_pages = out.parent / "screener_pages"
    canonical_summary = out.with_suffix(".summary.json")
    backup = run_dir / "previous_canonical"
    backup.mkdir(exist_ok=True)
    for path in (out, canonical_summary):
        if path.exists():
            shutil.copy2(path, backup / path.name)
    replacement = out.parent / (".screener_pages_" + run_dir.name)
    shutil.copytree(pages_dir, replacement)
    old_pages = backup / "screener_pages"
    if canonical_pages.exists():
        canonical_pages.rename(old_pages)
    try:
        replacement.rename(canonical_pages)
    except Exception:
        if old_pages.exists() and not canonical_pages.exists():
            old_pages.rename(canonical_pages)
        raise
    for staged, canonical in ((run_dir / out.name, out),
                              (run_dir / canonical_summary.name, canonical_summary)):
        temporary = canonical.with_name("." + canonical.name + ".new")
        shutil.copy2(staged, temporary)
        os.replace(temporary, canonical)


def compare_master(master_path: Path, rows: list[dict]):
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("Install pyarrow first: uv add pyarrow") from exc
    table = pq.read_table(master_path, columns=["instrument_id"])
    master_ids = set(table.column("instrument_id").to_pylist())
    screener_ids = {r["instrument_id"] for r in rows}
    return {
        "master_path": str(master_path),
        "master_unique_ids": len(master_ids),
        "screener_unique_ids": len(screener_ids),
        "in_master_not_screener": sorted(master_ids - screener_ids),
        "in_screener_not_master": sorted(screener_ids - master_ids),
    }


def find_screener_tab(context, initial_page, timeout_seconds: float = 15.0):
    """Find the live Screener tab after interactive login/navigation.

    While Python blocks inside input(), Playwright may not dispatch browser events.
    A Playwright call after input() lets page/popup/URL events be processed.
    Prefer verifying the actual Screener DOM over trusting cached page URLs.
    """
    deadline = time.monotonic() + timeout_seconds
    last_details = []
    while time.monotonic() < deadline:
        # Yield through Playwright so pending page/popup/navigation events get dispatched.
        if not initial_page.is_closed():
            initial_page.wait_for_timeout(500)
        else:
            time.sleep(0.5)
        tabs = list(context.pages)
        last_details = []
        for index, candidate in enumerate(tabs):
            try:
                if candidate.is_closed():
                    continue
                # Calling .count() triggers a browser round-trip; the URL cache is
                # now also updated by events dispatched during that round-trip.
                row_count = candidate.locator(ROW_SELECTOR).count()
                footer_present = bool(FOOTER_PATTERN.search(
                    candidate.locator("body").inner_text(timeout=5000)
                ))
                url = candidate.url
                last_details.append(
                    f"tab {index}: url={url!r}, screener_rows={row_count}, "
                    f"footer_present={footer_present}"
                )
                if row_count > 0 and footer_present:
                    print(f"  Using Screener tab: {url}")
                    return candidate
            except Exception as exc:
                last_details.append(f"tab {index}: error={type(exc).__name__}: {exc}")
        # Keep polling briefly to accommodate slow loads or a late popup.
    raise RuntimeError(
        "Could not locate a Playwright-controlled IRESS Screener tab. "
        "Make sure you used the browser opened by this script, not your normal "
        "Chrome window. Current tabs: " + "; ".join(last_details)
    )


def print_final_summary(summary: dict, out: Path, pages_dir: Path,
                        diagnostics_path: Path) -> None:
    reconciliation = summary.get("master_reconciliation")
    print("\n=== FINAL METADATA EXTRACTION SUMMARY ===")
    print(f"Screener rows captured: {summary['rows']}")
    print(f"Unique instrument IDs: {summary['unique_instrument_ids']}")
    print(f"Duplicate instrument IDs: {len(summary['duplicate_instrument_ids'])}")
    print(f"Pages successfully captured: {summary['pages_captured']}")
    print(f"Expected Screener result count: {summary['expected_screener_total']}")
    print(f"Pagination validation: {summary['pagination_validation']}")
    print(f"Duplicate-page validation: {summary['duplicate_page_validation']}")
    print("\nTHESIS RECONCILIATION")
    if reconciliation:
        print(f"Unique instruments in thesis: {reconciliation['master_unique_ids']}")
        print(f"Matched instruments: {reconciliation['master_unique_ids'] - len(reconciliation['in_master_not_screener'])}")
        print(f"Thesis-only instruments: {len(reconciliation['in_master_not_screener'])}")
        print(f"Screener-only instruments: {len(reconciliation['in_screener_not_master'])}")
        for label, key in (("Thesis-only IDs", "in_master_not_screener"),
                           ("Screener-only IDs", "in_screener_not_master")):
            ids = reconciliation[key]
            if len(ids) <= 20:
                print(f"{label}: {', '.join(ids) if ids else '(none)'}")
            else:
                print(f"{label}: {len(ids)} IDs; see {summary.get('unmatched_csv', 'summary JSON')}")
    else:
        print("No thesis master was supplied")
    print("\nISIN VALIDATION")
    for label, key in (("Nonempty ISIN values", "isin_nonempty_count"),
                       ("Valid ISIN format", "isin_format_valid_count"),
                       ("Invalid or placeholder ISIN values", "isin_format_invalid_count"),
                       ("Missing ISIN values", "isin_missing_count")):
        print(f"{label}: {summary[key]}")
    print("\nOUTPUTS")
    print(f"Metadata CSV: {out}")
    print(f"Summary JSON: {out.with_suffix('.summary.json')}")
    print(f"Page snapshots: {pages_dir}")
    print(f"Diagnostics JSON: {diagnostics_path}")
    print(f"\nFINAL STATUS: {summary['final_status']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("metadata/jse_screener_snapshot.csv"))
    parser.add_argument("--profile", type=Path, default=Path(".iress-screener-profile"))
    parser.add_argument("--master", type=Path, help="Optional instruments.parquet to reconcile against")
    parser.add_argument("--resume-run", type=Path,
                        help="Resume a staged run directory printed after an earlier failure")
    parser.add_argument("--viewport-width", type=int, default=1366,
                        help="Browser viewport width; default 1366")
    parser.add_argument("--viewport-height", type=int, default=720,
                        help="Browser viewport height; default 720")
    args = parser.parse_args()

    rows: list[dict] = []
    out = args.out.resolve()
    if args.resume_run:
        run_dir = args.resume_run.resolve()
        run_state = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        captured_at = run_state["captured_at"]
    else:
        now = datetime.now().astimezone()
        captured_at = now.isoformat(timespec="seconds")
        run_dir = out.parent / "screener_runs" / now.strftime("run_%Y%m%d_%H%M%S_%f")
        run_dir.mkdir(parents=True, exist_ok=False)
        run_state = {"captured_at": captured_at, "out": str(out), "expected_total": None}
        (run_dir / "run.json").write_text(json.dumps(run_state, indent=2) + "\n", encoding="utf-8")
    pages_dir = run_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Staging run: {run_dir}")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(args.profile.resolve()), headless=False,
            viewport={"width": args.viewport_width, "height": args.viewport_height},
        )
        page = context.pages[0] if context.pages else context.new_page()
        try:
            if page.url == "about:blank":
                page.goto(EXPERT_URL, wait_until="domcontentloaded", timeout=60000)
            print("\nIn the browser, sign in to IRESS Expert yourself if necessary.")
            print("Open Screener; select Type=Equities and Companies, Exchange=Jse Securities Exchange,")
            print("Listing Status=Listed AND Delisted; leave other filters clear.")
            input("When filtered Screener is on page 1, press Enter (script sets Show 100): ")

            page = find_screener_tab(context, page)

            ensure_100_results(page)
            first_snapshot = wait_for_page_snapshot(page, 1)
            start, end, total, _ = first_snapshot
            if start != 1 or end != 100:
                raise RuntimeError(f"Expected Screener page 1 with 100 results; got {start}-{end} of {total}.")
            if total < 100 or total > 10000:
                raise RuntimeError(f"Unexpected total {total}; verify Screener filters before collecting.")
            if run_state["expected_total"] is None:
                run_state["expected_total"] = total
                (run_dir / "run.json").write_text(
                    json.dumps(run_state, indent=2) + "\n", encoding="utf-8"
                )
            elif run_state["expected_total"] != total:
                raise RuntimeError(
                    f"Screener total changed from staged run's {run_state['expected_total']} "
                    f"to {total}; start a fresh run instead of resuming."
                )
            pages = (total + 99) // 100
            print(f"Capturing {total} rows in {pages} pages...")

            for page_no in range(1, pages + 1):
                expected_start = (page_no - 1) * 100 + 1
                first, last, count, extracted = (
                    first_snapshot if page_no == 1
                    else wait_for_page_snapshot(
                        page, expected_start,
                        seen_hrefs={r["landing_href"] for r in rows},
                    )
                )
                if count != total or first != expected_start or last != min(page_no * 100, total):
                    raise RuntimeError(f"Unexpected pagination state on page {page_no}: {first}-{last} of {count}")

                expected_n = last - first + 1
                if len(extracted) != expected_n:
                    raise RuntimeError(f"Page {page_no}: found {len(extracted)} rows, expected {expected_n}")
                page_rows = []
                for offset, item in enumerate(extracted):
                    if item["td_count"] != 8:
                        raise RuntimeError(f"Page {page_no} row {offset + 1}: expected 8 TDs: {item!r}")
                    instrument_id = decode_instrument_id(item["landing_href"])
                    record = {
                        "captured_at": captured_at,
                        "position": first + offset,
                        "instrument_id": instrument_id,
                        "company_name": item["company_name"],
                        "ticker": item["ticker"],
                        "isin": item["isin"],
                        "isin_format_valid": bool(re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", item["isin"])),
                        "instrument_type": item["instrument_type"],
                        "exchange": item["exchange"],
                        "country": item["country"],
                        "listing_status": item["listing_status"],
                        "landing_href": item["landing_href"],
                    }
                    page_rows.append(record)
                validate_page_records(page_rows, first, last, rows)
                saved_new = save_page_snapshot(
                    pages_dir / f"page_{page_no:02d}.json",
                    {"page": page_no, "first": first, "last": last, "total": total,
                     "captured_at": captured_at, "rows": page_rows},
                )
                rows.extend(page_rows)
                print(f"Page {page_no:02d}/{pages}: {first}-{last}, {len(page_rows)} rows"
                      + ("" if saved_new else " (verified saved snapshot)"))
                if page_no < pages:
                    # UI pagination only; no private network endpoints.
                    page.locator("#searchScreener_Results").get_by_text("Next", exact=True).click(timeout=30000)

            if len(rows) != total:
                raise RuntimeError(f"Captured {len(rows)} rows; Screener reported {total}")
            identifiers = [r["instrument_id"] for r in rows]
            repeated = sorted(key for key, count in Counter(identifiers).items() if count > 1)
            if repeated:
                raise RuntimeError(f"Repeated instrument IDs across pages: {repeated[:12]}")
            save_csv(run_dir / out.name, rows)
            nonempty_isin = sum(bool(r["isin"].strip()) for r in rows)
            valid_isin = sum(r["isin_format_valid"] for r in rows)
            summary = {
                "captured_at": captured_at,
                "filter_description": "JSE Securities Exchange / Equities and Companies / Listed and Delisted",
                "source": "IRESS Expert Screener visible UI",
                "snapshot_not_historical": True,
                "rows": len(rows), "unique_instrument_ids": len(set(identifiers)),
                "duplicate_instrument_ids": repeated,
                "pages_captured": pages, "expected_screener_total": total,
                "pagination_validation": "PASS", "duplicate_page_validation": "PASS",
                "isin_nonempty_count": nonempty_isin,
                "isin_format_valid_count": valid_isin,
                "isin_format_invalid_count": nonempty_isin - valid_isin,
                "isin_missing_count": len(rows) - nonempty_isin,
                "ticker_vs_identifier_mismatches": [r["instrument_id"] for r in rows
                    if r["ticker"] != r["instrument_id"].split(":", 1)[0]],
                "final_status": "PASS",
            }
            if args.master:
                summary["master_reconciliation"] = compare_master(args.master, rows)
                unmatched = summary["master_reconciliation"]
                if unmatched["in_master_not_screener"]:
                    summary["final_status"] = "FAIL"
                if (len(unmatched["in_master_not_screener"]) > 20
                        or len(unmatched["in_screener_not_master"]) > 20):
                    unmatched_path = out.parent / "screener_unmatched_ids.csv"
                    with (run_dir / unmatched_path.name).open(
                        "w", newline="", encoding="utf-8"
                    ) as f:
                        writer = csv.writer(f)
                        writer.writerow(["source", "instrument_id"])
                        for key, source in (("in_master_not_screener", "thesis_only"),
                                            ("in_screener_not_master", "screener_only")):
                            writer.writerows((source, instrument_id)
                                             for instrument_id in unmatched[key])
                    summary["unmatched_csv"] = str(unmatched_path)
            summary["csv_sha256"] = hashlib.sha256((run_dir / out.name).read_bytes()).hexdigest()
            report = out.with_suffix(".summary.json")
            (run_dir / report.name).write_text(
                json.dumps(summary, indent=2) + "\n", encoding="utf-8"
            )
            diagnostics_path = out.parent / "screener_diagnostics.json"
            original_diagnostics = out.parent / "screener_diagnostics_original.json"
            if diagnostics_path.exists() and not original_diagnostics.exists():
                shutil.copy2(diagnostics_path, original_diagnostics)
            promote_run(run_dir, out, pages_dir)
            if summary.get("unmatched_csv"):
                shutil.copy2(run_dir / "screener_unmatched_ids.csv",
                             summary["unmatched_csv"])
            if args.master:
                from iress_screener_diagnostics import audit
                audit_report = audit(out.parent / "screener_pages", out, report, args.master)
                diagnostics_path.write_text(
                    json.dumps(audit_report, indent=2) + "\n", encoding="utf-8"
                )
            print_final_summary(summary, out, out.parent / "screener_pages",
                                diagnostics_path)
        except Exception as exc:
            try:
                page.screenshot(path=str(run_dir / "screener_error.png"), full_page=True)
                (run_dir / "screener_error.txt").write_text(
                    f"Error: {exc}\nURL: {page.url}\nPages captured: {len(rows) // 100}\n"
                    f"Layout diagnostic: {json.dumps(debug_layout(page), indent=2)}\n",
                    encoding="utf-8",
                )
            except Exception:
                pass
            print(f"\nSTOPPED: {exc}\nValidated page JSON files stay in {pages_dir}. "
                  f"Resume with --resume-run {run_dir}", file=sys.stderr)
            raise
        finally:
            context.close()


if __name__ == "__main__":
    main()
