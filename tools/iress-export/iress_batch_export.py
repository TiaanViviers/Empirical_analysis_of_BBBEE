#!/usr/bin/env python3
"""IRESS Expert UI batch exporter (v6; robust name-based field selection).

USAGE (from a project with playwright and openpyxl installed):
    uv run python iress_batch_export.py --start 1 --end 2
    uv run python iress_batch_export.py --start 1 --end 19
    uv run python iress_batch_export.py --validate-only "Comparison-Raw-Report (5).xlsx"

Uses a separate, persistent Chromium profile. Sign in yourself in the browser
when prompted; no credentials belong in the source code. Use only if permitted
by your university's and IRESS's data access terms.

CAUTION: Exact locators are based on Codegen recordings, not a live IRESS session.
Test batches 1–2 first and refine selectors when the interface requires it.
"""

import argparse
from collections import Counter
import csv
from datetime import date, datetime
import json
from pathlib import Path
import re
import sys
import time

from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

EXPERT_URL = "https://expert-iress-co-za.ez.sun.ac.za/"
FIELDS = ("Mnemonic", "Company", "Date", "Close", "Number Of Trades", "Volume")
SELECTED_FIELD_ROWS = (
    ".selectedfields .fields "
    "li[data-view='views/instruments/fieldselection/selectionField']"
)
STUDY_START = date(2016, 1, 1)
STUDY_END = date(2026, 3, 31)
PAGE_SIZE = 100
LAST_BATCH = 19
LEGACY_SCREENER_TOTAL = 1870  # Existing manifest entries predate count tracking.


def as_date(value, epoch):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        return from_excel(value, epoch=epoch).date()
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(value.strip()[:10], fmt).date()
            except ValueError:
                pass
    raise ValueError(f"Unrecognised date value: {value!r}")


def validate_workbook(path, expected_instruments=None):
    """Stream-read the downloaded workbook. Never interpret blanks as trades."""
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = wb.active
        iterator = sheet.iter_rows(values_only=True)
        headers = next(iterator, None)
        if not headers:
            raise ValueError("Workbook is empty")
        labels = [str(h).strip() if h is not None else "" for h in headers]
        if set(labels) != set(FIELDS) or len(labels) != len(FIELDS):
            raise ValueError(f"Unexpected columns: {labels!r}; wanted {FIELDS!r}")
        ix = {k: labels.index(k) for k in FIELDS}

        instruments = {}
        dates = set()
        counts = Counter()
        seen_pairs = set()
        duplicate_pairs = 0
        row_count = 0
        for row in iterator:
            if not any(x is not None for x in row):
                continue
            row_count += 1
            ident = str(row[ix["Mnemonic"]] or "").strip()
            company = str(row[ix["Company"]] or "").strip()
            if not ident:
                raise ValueError(f"Missing instrument identifier at data row {row_count}")
            instruments[ident] = company
            d = as_date(row[ix["Date"]], wb.epoch)
            dates.add(d)
            counts[ident] += 1
            pair = (ident, d)
            if pair in seen_pairs:
                duplicate_pairs += 1
            seen_pairs.add(pair)

        if duplicate_pairs:
            raise ValueError(f"{duplicate_pairs} duplicate instrument-date rows")
        if expected_instruments is not None and len(instruments) != expected_instruments:
            raise ValueError(
                f"Expected {expected_instruments} instruments; downloaded {len(instruments)}"
            )
        if not dates or not (date(2016, 1, 3) <= min(dates) <= date(2016, 1, 15)):
            raise ValueError(f"Incorrect starting date: {min(dates) if dates else 'none'}")
        if max(dates) < date(2026, 3, 25) or max(dates) > STUDY_END:
            raise ValueError(f"Incorrect ending date: {max(dates)}")
        if len(dates) < 2400:
            raise ValueError(
                f"Only {len(dates)} distinct dates. Possibly weekly data or truncated export."
            )
        if row_count < 2200 * len(instruments):
            raise ValueError(
                f"Only {row_count} rows for {len(instruments)} instruments: "
                "review completeness before accepting"
            )
        return {
            "instruments": instruments,
            "instrument_count": len(instruments),
            "row_count": row_count,
            "unique_dates": len(dates),
            "start": min(dates).isoformat(),
            "end": max(dates).isoformat(),
            "min_rows_per_instrument": min(counts.values()),
            "max_rows_per_instrument": max(counts.values()),
        }
    finally:
        wb.close()


def load_manifest(path):
    return json.loads(path.read_text()) if path.exists() else {}


def write_manifest(path, data):
    staged = path.with_suffix(".pending.json")
    staged.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    staged.replace(path)


def check_cross_batch_overlap(manifest, batch_number, identifiers):
    current = set(identifiers)
    for prior_key, info in manifest.items():
        if int(prior_key) == batch_number:
            continue
        overlap = current.intersection(info.get("instruments", {}))
        if overlap:
            print(
                f"  WARNING: {len(overlap)} instruments in batch {batch_number:02d} "
                f"also appear in batch {int(prior_key):02d}: "
                f"{sorted(overlap)[:8]}. Deduplicate after export.",
                file=sys.stderr,
                flush=True,
            )


def wait_for_screener(page, timeout_ms=45000):
    """Confirm the actual Screener view rendered, not merely that nav was clicked.

    IRESS is a single-page application. Its navigation click can finish before
    the new view has rendered. The original script immediately clicked 'Add',
    which can time out if the Markets page is still displayed.
    """
    heading = page.get_by_text(re.compile(r"Search\s+Screener", re.I)).first
    heading.wait_for(state="visible", timeout=timeout_ms)
    page.get_by_role("link", name="Add").first.wait_for(
        state="visible", timeout=timeout_ms
    )


def enter_screener(page):
    """Navigate to Screener and wait for its filter panel, with one retry."""
    nav = page.get_by_role("link", name="Screener", exact=True)
    nav.wait_for(state="visible", timeout=45000)
    print(f"  IRESS before Screener navigation: {page.url}", flush=True)

    # Do not reset the whole app with page.goto(EXPERT_URL) between batches.
    # That caused the previous run to leave the browser on Markets.
    for attempt in (1, 2):
        print(f"  Opening Screener (attempt {attempt})...", flush=True)
        nav.click(timeout=15000)
        try:
            wait_for_screener(page, timeout_ms=20000)
            print(f"  Screener loaded: {page.url}", flush=True)
            return
        except PlaywrightTimeoutError:
            print(
                f"  Screener filters not yet visible after navigation. "
                f"Current URL: {page.url}",
                flush=True,
            )
            # May have landed on a different SPA route. Retry clicking the
            # real navigation link once; never silently apply filters elsewhere.
    try:
        snippet = page.locator("body").inner_text(timeout=3000)[:800]
    except Exception:
        snippet = "<unavailable>"
    raise RuntimeError(
        "IRESS did not render the Screener filter panel after two attempts. "
        f"URL: {page.url}\nVisible page text: {snippet!r}\n"
        "See exports/error_batch_XX.png and exports/error_batch_XX.txt."
    )


def setup_screener(page):
    """Rebuild all filters because IRESS does not preserve them after Compare."""
    enter_screener(page)

    print("  Configuring Type filter...", flush=True)
    # Instrument type: Equities and Companies (recorded by user)
    page.get_by_role("link", name="Add").first.click()
    page.locator(".icon.i-tree-closed").click()
    page.locator(
        ".durandal-wrapper > div > ul > li > .durandal-wrapper > "
        ".with-tooltip > .icon_base.icon_plus"
    ).first.click()
    page.get_by_role("button", name="Save").click()

    print("  Configuring Exchange filter...", flush=True)
    # Exchange: JSE Securities Exchange (recorded by user)
    page.get_by_role("link", name="Add").first.click()
    page.get_by_role("textbox", name="Filter list").fill("JSE")
    page.locator(
        "li:nth-child(18) > .durandal-wrapper > .with-tooltip > "
        ".icon_base.icon_plus"
    ).click()
    page.get_by_role("button", name="Save").click()

    print("  Configuring Listing Status filter...", flush=True)
    # Listing status: Listed + Delisted (recorded by user)
    page.get_by_role("link", name="Add").nth(2).click()
    page.locator(".icon_base.icon_plus").first.click()
    page.locator(
        "li:nth-child(3) > .durandal-wrapper > .with-tooltip > "
        ".icon_base.icon_plus"
    ).click()
    page.get_by_role("button", name="Save").click()

    print("  Setting Screener page size to 100...", flush=True)
    # Screener pagination size: Show 100 Results
    page.locator("dt > .icon").click()
    # Both the displayed value (<dt>) and dropdown option (<dd><a>) can
    # contain "100". The option's <a> has no href, so it has no link role.
    page.get_by_role("definition").get_by_text("100", exact=True).click()
    # verify_screener_page checks the resulting 1-100 page before selection.


def verify_screener_page(page, page_number, expected_total=None):
    """Use the visible results counter to prove the correct batch is on screen."""
    wanted_first = 1 + (page_number - 1) * PAGE_SIZE
    pattern = re.compile(
        r"Displaying Results\s+([\d,]+)\s*-\s*([\d,]+)\s+of\s+([\d,]+)",
        re.IGNORECASE,
    )
    last_seen = None
    for _ in range(50):
        text = page.locator("body").inner_text()
        match = pattern.search(text)
        if match:
            first, last, total = (
                int(value.replace(",", "")) for value in match.groups()
            )
            last_seen = (first, last, total)
            if first == wanted_first and last == min(page_number * PAGE_SIZE, total):
                if not (1800 < total <= LAST_BATCH * PAGE_SIZE):
                    raise ValueError(
                        f"Screener has {total:,} results, outside the expected "
                        f"{LAST_BATCH}-page range. Check the filters and batch limit."
                    )
                if expected_total is not None and total != expected_total:
                    raise ValueError(
                        f"Screener result count changed during pagination "
                        f"from {expected_total:,} to {total:,}; batch {page_number} "
                        "could contain the wrong instruments."
                    )
                return total
        page.wait_for_timeout(250)
    raise ValueError(
        f"Screener not on page {page_number}, or filters/count changed. "
        f"Wanted page {page_number} of a {LAST_BATCH}-page list; "
        f"last counter seen: {last_seen!r}."
    )


def goto_screener_page(page, batch, expected_total=None):
    # Screenshot of the user's IRESS pager confirms a 'Next' control.
    # Clicking Next repeatedly also works after the numbered pages 1-8 vanish.
    total = verify_screener_page(page, 1, expected_total)
    results = page.locator("#searchScreener_Results")
    for number in range(2, batch + 1):
        results.get_by_text("Next", exact=True).click()
        verify_screener_page(page, number, total)
    first = 1 + (batch - 1) * PAGE_SIZE
    last = min(batch * PAGE_SIZE, total)
    print(
        f"  Screener page {batch} verified: results "
        f"{first:,}-{last:,} of {total:,}",
        flush=True,
    )
    return total

def open_comparison(page):
    page.get_by_text("▼", exact=True).click()
    menu = page.get_by_role("link", name="Deselect All")
    if menu.is_visible():
        menu.click()
        page.get_by_text("▼", exact=True).click()
    page.get_by_role("link", name="Select Visible").click()
    page.get_by_role("link", name="Tools").click()
    page.get_by_role("link", name="Compare (max 400 instruments)").click()


def click_edit_fields(page):
    """Locate the *visible* Edit Fields control; fail with useful evidence.

    An earlier run timed out on get_by_role('link', name='Edit Fields').
    That doesn't prove the control isn't displayed: IRESS may render it
    with a different HTML role, or the Comparison view may not be ready.
    """
    candidates = [
        ("visible text", page.get_by_text("Edit Fields", exact=True)),
        ("button role", page.get_by_role("button", name="Edit Fields")),
        ("link role", page.get_by_role("link", name="Edit Fields")),
    ]
    for _ in range(50):  # ~25 seconds maximum, allowing for SPA updates
        for label, locator in candidates:
            try:
                if locator.count() > 0 and locator.first.is_visible():
                    print(f"Opening Edit Fields via {label}", flush=True)
                    locator.first.click(timeout=5000)
                    return
            except PlaywrightTimeoutError:
                pass
        page.wait_for_timeout(500)

    # This is deliberately a hard stop. Continuing without knowing which
    # page we're on risks silently exporting the wrong company/date data.
    try:
        summary = page.locator("body").inner_text(timeout=5000)
        summary = summary[:1000].replace("\n", " | ")
    except Exception:
        summary = "<body text unavailable>"
    raise RuntimeError(
        "Edit Fields not visible after selecting Daily. "
        f"Current URL: {page.url}\n"
        f"Beginning of visible page text: {summary}\n"
        "Please upload exports/error_batch_02.png to diagnose whether "
        "the Comparison screen or date picker is still open."
    )


def selected_field_names(page):
    """Wait for IRESS to populate the editor, then read its field captions."""
    rows = page.locator(SELECTED_FIELD_ROWS)
    rows.first.wait_for(state="visible", timeout=15000)
    return [
        re.sub(r"\s+", " ", caption).strip()
        for caption in rows.locator("span[data-bind='text: caption']").all_inner_texts()
    ]


def wait_for_selected_field(page, name, present):
    """Wait for the editor's selected list to reflect a click."""
    for _ in range(60):
        names = selected_field_names(page)
        if (name in names) == present:
            return
        page.wait_for_timeout(250)
    raise RuntimeError(
        f"Field {name!r} did not become {'selected' if present else 'unselected'}; "
        f"selected fields: {selected_field_names(page)!r}"
    )


def remove_selected_field(page, name):
    """Click the purple remove icon beside one explicitly named field."""
    exact = re.compile(r"^\s*" + re.escape(name) + r"\s*$")
    rows = page.locator(SELECTED_FIELD_ROWS).filter(has_text=exact)
    if rows.count() != 1:
        raise RuntimeError(
            f"Cannot uniquely identify selected field {name!r}: "
            f"{rows.count()} matching LI elements. "
            f"Panel text: {page.locator('.selectedfields').inner_text()!r}"
        )
    icon = rows.first.locator(":scope > .icon_base.icon_remove")
    if icon.count() != 1:
        raise RuntimeError(f"Cannot find remove icon for field {name!r}")
    icon.click()
    wait_for_selected_field(page, name, present=False)


def add_market_field(page, name):
    """Find a field by its label in the available list, not its LI index."""
    exact = re.compile(r"^\s*" + re.escape(name) + r"\s*$")
    matches = page.locator("li").filter(has_text=exact)
    candidates = []
    for i in range(matches.count()):
        row = matches.nth(i)
        if not row.is_visible():
            continue
        # The turquoise plus belongs to the available-fields list. The
        # selected list uses a purple remove icon for the same field name.
        icon = row.locator(":scope > .icon_base.icon_plus")
        if icon.count() == 1 and icon.is_visible():
            candidates.append(icon)
    if len(candidates) != 1:
        raise RuntimeError(
            f"Could not uniquely identify add icon for {name!r}: "
            f"{len(candidates)} candidates among {matches.count()} matching LI "
            "elements. Inspect the available-fields list HTML."
        )
    candidates[0].click()
    wait_for_selected_field(page, name, present=True)


def setup_comparison(page):
    # Preserve the user's working Codegen sequence for the two calendar pickers.
    page.get_by_text("Custom", exact=True).click()
    # Codegen recorded `.icon_base.first`, but that selector can pick a hidden
    # information tooltip rather than the start-date calendar icon. Clicking
    # the named start-date textbox directly is a more stable way to open it.
    start_date_input = page.get_by_role("textbox", name="Custom")
    start_date_input.wait_for(state="visible", timeout=15000)
    start_date_input.click()
    page.get_by_role("combobox").nth(1).select_option("2016")
    page.get_by_role("combobox").first.select_option("0")
    page.get_by_role("link", name="1", exact=True).click()

    page.locator("label:nth-child(2) > .icon_base").click()
    page.get_by_role("textbox", name="to", exact=True).click()
    # Explicitly set the end year instead of relying on the current year.
    page.get_by_role("combobox").nth(1).select_option("2026")
    page.get_by_role("combobox").first.select_option("2")
    page.get_by_role("link", name="31", exact=True).click()
    page.get_by_role("button", name="Save").click()

    # Set Daily *after* Custom; otherwise the site may export weekly data.
    page.locator("dt > .icon").click()
    page.get_by_text("Daily", exact=True).click()
    page.wait_for_timeout(700)  # allow IRESS to update the comparison report

    # IRESS can expose Edit Fields as a link, a button, or plain clickable
    # text depending on which version of the Comparison view is rendered.
    # Prefer the exact visible text rather than assuming the ARIA role.
    click_edit_fields(page)
    # Configure fields by their *names* rather than the former brittle
    # `li:nth-child(3)` and `li:nth-child(81)` selectors. This also works if
    # IRESS retains some previously chosen fields between runs.
    desired = {"Close", "Number Of Trades", "Volume"}
    initial = selected_field_names(page)
    print(f"  Selected fields on opening editor: {initial}", flush=True)
    for name in initial:
        if name not in desired:
            print(f"  Removing unwanted field: {name}", flush=True)
            remove_selected_field(page, name)

    for name in ("Close", "Volume", "Number Of Trades"):
        if name not in selected_field_names(page):
            print(f"  Adding required field: {name}", flush=True)
            add_market_field(page, name)

    selected_names = selected_field_names(page)
    print(f"  Selected fields before saving: {selected_names}", flush=True)
    if len(selected_names) != 3 or set(selected_names) != desired:
        raise RuntimeError(
            f"Edit Fields selection is wrong: {selected_names!r}; "
            f"expected exactly {sorted(desired)!r}. "
            f"Selected-fields panel text: "
            f"{page.locator('.selectedfields').inner_text()!r}. "
            "No export was attempted."
        )

    print("  Saving Edit Fields changes...", flush=True)
    # Save belongs to the Edit Fields dialog. Don't export until it closes.
    page.get_by_role("link", name="Save", exact=True).click()
    page.locator(".selectedfields").wait_for(state="hidden", timeout=45000)
    print("  Field editor closed; ready to export", flush=True)



def export_download(page, target):
    page.get_by_role("link", name="Tools").click()
    page.get_by_role("link", name="Export for Excel").click()
    # One click, not the duplicated click in the Codegen recording.
    with page.expect_download(timeout=300000) as event:
        page.get_by_role("button", name="Download Report").first.click()
    download = event.value
    failure = download.failure()
    if failure:
        raise RuntimeError(f"IRESS download failed: {failure}")
    download.save_as(str(target))  # blocks until the download is saved


def run_batches(args):
    output = Path(args.output).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "export_manifest.json"
    manifest = load_manifest(manifest_path)
    previous_total = None
    if manifest:
        latest_batch = max(manifest, key=int)
        previous_total = manifest[latest_batch].get(
            "screener_total", LEGACY_SCREENER_TOTAL
        )

    with sync_playwright() as playwright:
        profile = Path(args.profile).expanduser().resolve()
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            headless=False,
            accept_downloads=True,
            viewport={"width": 1440, "height": 950},
        )
        context.set_default_timeout(30000)
        page = context.pages[0] if context.pages else context.new_page()
        try:
            if not any("expert-iress-co-za.ez.sun.ac.za" in p.url for p in context.pages):
                page.goto(EXPERT_URL, wait_until="domcontentloaded")
            try:
                ready_pages = [p for p in context.pages
                               if "expert-iress-co-za.ez.sun.ac.za" in p.url]
                if ready_pages:
                    page = ready_pages[-1]
                page.get_by_role("link", name="Screener", exact=True).wait_for(
                    state="visible", timeout=12000
                )
            except PlaywrightTimeoutError:
                print("\nPlease finish login in the opened browser, then press Enter.")
                print("If direct access fails, navigate via SU Library within this browser.")
                input("Logged in and on IRESS Expert? Press Enter: ")
                ready_pages = [p for p in context.pages
                               if "expert-iress-co-za.ez.sun.ac.za" in p.url]
                if not ready_pages:
                    raise RuntimeError("No IRESS Expert tab found after login")
                page = ready_pages[-1]
                page.get_by_role("link", name="Screener", exact=True).wait_for(
                    state="visible", timeout=45000
                )
            print(f"  Using IRESS tab: {page.url}", flush=True)

            for batch in range(args.start, args.end + 1):
                final = output / f"jse_prices_{batch:02d}.xlsx"
                print(f"\n=== Batch {batch:02d} / 19 ===", flush=True)

                if final.exists():
                    prior = manifest.get(str(batch), {})
                    accepted_shortfall = (
                        prior.get("status") == "validated_with_missing_instrument"
                    )
                    expected = (
                        prior["instrument_count"] if accepted_shortfall else
                        (PAGE_SIZE if batch < LAST_BATCH else
                         prior.get("instrument_count"))
                    )
                    info = validate_workbook(final, expected)
                    check_cross_batch_overlap(manifest, batch, info["instruments"])
                    manifest[str(batch)] = {
                        **prior,
                        **info,
                        "file": final.name,
                        "status": ("validated_with_missing_instrument"
                                   if accepted_shortfall else "validated_existing"),
                    }
                    write_manifest(manifest_path, manifest)
                    label = "Already accepted" if accepted_shortfall else "Already valid"
                    print(f"{label}: {final} ({info['row_count']:,} rows)")
                    continue

                staged = output / f"_pending_jse_prices_{batch:02d}.xlsx"
                try:
                    setup_screener(page)
                    total = goto_screener_page(page, batch)
                    if previous_total is not None and total != previous_total:
                        print(
                            f"  NOTE: Screener total changed from "
                            f"{previous_total:,} to {total:,}; continuing in "
                            "this output directory as requested.",
                            flush=True,
                        )
                    previous_total = total
                    expected = min(PAGE_SIZE, total - (batch - 1) * PAGE_SIZE)
                    open_comparison(page)
                    setup_comparison(page)
                    export_download(page, staged)
                    info = validate_workbook(staged, expected)
                    check_cross_batch_overlap(manifest, batch, info["instruments"])
                    staged.replace(final)
                    manifest[str(batch)] = {
                        **info,
                        "file": final.name,
                        "status": "validated",
                        "screener_total": total,
                    }
                    write_manifest(manifest_path, manifest)
                    print(
                        f"PASS: {final.name}, {info['instrument_count']} instruments, "
                        f"{info['row_count']:,} rows, {info['unique_dates']} dates"
                    )
                except Exception as exc:
                    try:
                        page.screenshot(path=str(output / f"error_batch_{batch:02d}.png"),
                                        full_page=True)
                    except Exception:
                        pass
                    try:
                        visible = page.locator("body").inner_text(timeout=4000)[:6000]
                    except Exception:
                        visible = "<could not read page text>"
                    try:
                        links = page.get_by_role("link").evaluate_all(
                            "els => els.slice(0, 35).map(e => ({text: e.innerText, href: e.getAttribute('href')}))"
                        )
                    except Exception:
                        links = []
                    try:
                        editor_html = page.locator(
                            ".selectedfields"
                        ).evaluate("el => el.outerHTML")[:20000]
                    except Exception:
                        editor_html = "<field editor not available>"
                    diagnostic = {
                        "url": page.url,
                        "title": page.title() if not page.is_closed() else "<closed>",
                        "visible_text": visible,
                        "links": links,
                        "selected_fields_html": editor_html,
                        "error": str(exc),
                    }
                    (output / f"error_batch_{batch:02d}.txt").write_text(
                        json.dumps(diagnostic, indent=2, ensure_ascii=False)
                    )
                    print(f"  Failure URL: {page.url}", file=sys.stderr)
                    if staged.exists():
                        print(f"Unvalidated file retained for inspection: {staged}")
                    print(f"STOPPED at batch {batch:02d}: {exc}", file=sys.stderr)
                    raise
        finally:
            context.close()


def main():
    parser = argparse.ArgumentParser(description="IRESS Expert batch export")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=2,
                        help="Default: test batches 1-2; use 19 for the full run")
    parser.add_argument("--output", default="exports")
    parser.add_argument("--profile", default=".iress-profile")
    parser.add_argument("--validate-only", type=Path,
                        help="Check an existing Excel export without opening a browser")
    args = parser.parse_args()
    if args.validate_only:
        info = validate_workbook(args.validate_only)
        print(json.dumps({k: v for k, v in info.items() if k != "instruments"},
                         indent=2))
        return
    if not (1 <= args.start <= args.end <= 19):
        parser.error("Batch range must satisfy 1 <= start <= end <= 19")
    run_batches(args)


if __name__ == "__main__":
    main()
