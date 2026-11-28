"""Researcher-facing audit, generated from observed counts rather than estimates."""

from typing import Any

from .config import Config


def table(headers: list[str], rows: list[list[Any]]) -> str:
    def cell(x: Any) -> str:
        return str(x if x is not None else "unavailable").replace("|", " / ")
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *["| " + " | ".join(cell(x) for x in row) + " |" for row in rows],
    ])


def pct(n: int, d: int) -> str:
    return f"{100*n/d:.2f}%" if d else "unavailable"


def bar_chart(cfg: Config, counts: dict[str, int]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    keys = ["0", "1-149", "150-999", "1000-2499", "2500+"]
    values = [counts.get(k, 0) for k in keys]
    # Stable SVG identifiers and no embedded wall-clock timestamp.
    with plt.rc_context({"svg.hashsalt": "iress-phase1", "svg.fonttype": "none"}):
        fig, ax = plt.subplots(figsize=(8, 3.8), layout="constrained")
        ax.barh(keys, values, color="#28789b")
        ax.invert_yaxis()
        ax.set_xlabel("Number of instruments")
        ax.set_ylabel("Valid price observations")
        ax.set_title("Historical price coverage")
        maximum = max(values, default=1) or 1
        ax.set_xlim(0, maximum * 1.15)
        for i, value in enumerate(values):
            ax.text(value + maximum*.015, i, f"{value:,}", va="center")
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        fig.savefig(cfg.reports / "price_coverage.svg", metadata={
            "Date": None, "Creator": "iress_data Phase 1",
            "Title": "Historical price coverage", "Description": "Instrument counts by positive finite close observations"})
        fig.savefig(cfg.reports / "price_coverage.png", dpi=150, metadata={"Software": "iress_data Phase 1"})
        plt.close(fig)


def write_report(cfg: Config, s: dict[str, Any], instruments: list[dict[str, Any]]) -> None:
    g, t, m, d = s["global"], s["diagnostic_totals"], s["market_index"], s["duplicates"]
    n = g["unique_instruments"]
    valid = t["valid_price_observations"]
    observed = t["observations"]
    batches = s["batch_audit"]
    events = s["events"]
    if m.get("daily_benchmark_validated"):
        benchmark_status = "**Benchmark calendar validated:** Daily J203 matches every observed company session. Market-paired coverage is reported below; the return variant remains unverified."
    elif m.get("daily_frequency_validated"):
        benchmark_status = (f"**Daily benchmark with a documented gap:** J203 is daily with {m['rows']:,} valid observed levels, "
            f"but misses {m['company_dates_missing_from_index']} company sessions: {m['missing_company_dates']}. "
            "The full company calendar is retained, and returns never bridge the missing session. "
            "Market-paired coverage is checked separately for each event's actual windows.")
    else:
        benchmark_status = "**Blocking benchmark finding:** The supplied benchmark does not pass daily validation. Event counts use the company-calendar proxy and are not verified market-paired sample sizes."
    extra_fields = sorted(set(m.get("source_columns", [])) - {"Mnemonic","Company","Date","Close","Number Of Trades","Volume"})
    benchmark_layout = (f"Source benchmark columns: {m.get('source_columns',[])}. "
        + (f"Extra fields {extra_fields} remain in the original workbook. " if extra_fields else "The benchmark uses the six-column Flat Data Table layout. ")
        + "Index trade counts are not used as a liquidity screen. Missing benchmark levels are never interpolated or forward-filled.")
    bar_chart(cfg, s["price_coverage_distribution"])
    event_rows = []
    for r in events:
        if r["definition"] == "adjacent_prices":
            liquid = next(x for x in events if x["event_id"] == r["event_id"] and x["definition"] == "both_positive_volume")
            event_rows.append([r["event_date"], r["event_name"], r["any_near_price"],
                               r["any_near_price_and_positive_volume"],
                               r["estimation_ge_150"], r["estimation_ge_180"], r["estimation_ge_200"],
                               r["est180_and_complete_m10_10"], liquid["est180_and_complete_m10_10"]])
    sections = [
        "# IRESS JSE historical data: Phase 1 audit",
        "This report audits the supplied exports. It does not construct the thesis sample, infer listing dates, adjust returns, or estimate policy effects. All five event dates remain provisional.",
        "## Executive findings",
        table(["Measure", "Observed result"], [
            ["Company workbook rows", f"{g['raw_rows']:,}"],
            ["Unique IRESS instruments", f"{n:,}"],
            ["Distinct source company names", f"{g['unique_company_names']:,} (names are not verified companies)"],
            ["Observed calendar", f"{s['calendar']['start']} to {s['calendar']['end']}; {s['calendar']['unique_dates']:,} sessions"],
            ["Numerically valid positive prices", f"{valid:,} ({pct(valid,observed)} of diagnostic rows)"],
            ["Instruments with any valid price", s["instruments_with_valid_prices"]],
            ["Instruments without any valid price", s["instruments_without_valid_prices"]],
            ["Instruments with all three financial fields always blank", s["instruments_all_fields_missing"]],
            ["Instruments ever reporting positive volume", s["instruments_with_positive_volume"]],
            ["Identical duplicate keys / conflicting keys", f"{d['identical_duplicate_keys']:,} / {d['conflicting_keys']:,}"],
            ["J203 benchmark", f"{m.get('rows','unavailable')} rows; {m.get('frequency','unavailable')}; daily validation: {m['daily_benchmark_validated']}"],
        ]),
        benchmark_status,
        "## Extraction and calendar integrity",
        table(["Batch", "Rows", "Instruments", "Expected", "Dates", "Extra duplicate rows", "Manifest matches"], [
            [r["source_batch"], r.get("rows"), r.get("instruments"), r.get("expected_instruments"),
             r.get("unique_dates"), r.get("duplicate_extra_rows"), r.get("manifest_counts_match")]
            for r in batches]),
        f"Missing batches: {s['missing_batches']}. Unexpected batches: {s['unexpected_batches']}. Input failures: {s['input_failures']}. All batch date sets match: {s['all_batch_calendars_match']}. Manifest counts match actual workbook counts: {s['manifest_all_counts_match']}.",
        "The company headers are Mnemonic, Company, Date, Close, Number Of Trades, Volume. Source-type counts and actual column order are recorded for every workbook in batch_audit.csv and audit_summary.json. Native Excel dates are parsed with the workbook epoch. Numeric cells are preserved as Float64, including zeros and negative values; unparseable tokens are retained in unparsed_values and flagged. No missing value is converted to zero.",
        f"The company calendar is {s['calendar']['frequency']}, with {s['calendar']['weekend_dates']} weekend dates. Calendar-day gap distribution: {s['calendar']['gap_days']}. A common weekday-shaped calendar supports daily frequency, but is not independent exchange-calendar verification. Boundary holidays are not expected observations merely because the request starts on 1 January.",
        "Batch 19 must be assessed against its manifest count, rather than against a full batch of 100. Batch 13's manifest labels Pbt Group Limited as missing; that is an extraction-log assertion, not a confirmed missing security. manifest_name_candidates.csv lists observed names sharing a first token for review. The manifest's later screener total is 1,872; earlier exports predate that count tracking. Differences from the screener total can include omitted instruments, repeated instruments and name/selection discrepancies. An identifier-level screener snapshot is needed to prove universe completeness.",
        table(["Manifest missing-name assertion", "Observed instrument", "Observed source name (unverified identity match)"],
              [[r['manifest_missing_name'],r['observed_instrument_id'],r['observed_company_name']] for r in s['manifest_missing_name_candidates']]),
        f"The files contain {s['batch_instrument_appearances']:,} batch-level instrument appearances and {n:,} distinct IDs, versus a latest recorded screener count of {s['latest_recorded_screener_total']}. A screener count alone does not identify which records differ or prove that every screener result maps to a distinct security. Review the PBT naming discrepancy before requesting a supposedly missing instrument again.",
        "## Duplicates and identities",
        f"There are {d['overlapping_or_repeated_instruments']} instruments repeated within/across batches, {d['duplicate_keys']:,} repeated instrument-date keys, and {d['duplicate_extra_rows']:,} extra rows. There are {d['conflicting_keys']:,} conflicting keys. Equality checks include company name, all three financial fields and parse tokens. conflicting_observations.csv retains every source copy for conflicting keys; an empty report still has headers.",
        "Raw intermediate Parquet retains every source observation. For audit statistics only, identical copies count once, ordered by filename, sheet and source row. All copies of conflicting keys are excluded from numerical diagnostics and remain in the conflict report. This audit convention is not a finalized curated-data policy. Recommendation: accept deterministic identical-copy reduction with a separate all-source lineage table; stop any future build when conflicts lack an explicit resolution.",
        table(["Repeated instrument", "Source name", "Batches", "Extra rows"],
              [[r['instrument_id'],r['company_names'],r['source_batches'],r['extra_rows']] for r in d['examples']]),
        f"{s['same_name_multiple_instrument_groups']} exact company-name groups map to multiple instruments; {s['instruments_with_multiple_names']} instruments have multiple observed names. See company_identity_candidates.csv and instrument_name_variants.csv. Identifier suffix counts: {s['instrument_suffixes']}. Source names repeated over the calendar do not establish historical name validity. Similar names, preference-share wording and mnemonic suffixes do not establish a verified company or security-type mapping. Keep share classes separate.",
        "## Missingness and useful history",
        "![Price coverage distribution](price_coverage.svg)",
        table(["Valid price observations per instrument", "Instruments"], [[k, s['price_coverage_distribution'].get(k,0)] for k in ("0","1-149","150-999","1000-2499","2500+")]),
        f"Of {observed:,} diagnostic observations, {t['missing_close']:,} have missing closes ({pct(t['missing_close'],observed)}), {t['missing_volume']:,} missing volumes ({pct(t['missing_volume'],observed)}), and {t['missing_trade_count']:,} missing trade counts ({pct(t['missing_trade_count'],observed)}). There are {t['all_fields_missing_rows']:,} rows with all three financial fields blank ({pct(t['all_fields_missing_rows'],observed)}). There are {t['positive_volume_days']:,} positive-volume observations and {t['zero_volume_days']:,} explicit zero-volume observations. {s['instruments_with_prices_but_no_positive_volume']} instruments have valid prices but no positive volume anywhere in the extracted period.",
        "The first/last valid-price and positive-volume dates describe data availability, not actual listing/delisting. Complete placeholder calendars are not evidence that securities were listed throughout. instrument_coverage.csv gives counts, missing percentages, longest missing-price and no-positive-volume runs, constant-price runs and all original provenance batches/files per instrument. raw_source_rows and raw_rows_excluded_from_numeric_diagnostics reconcile source copies to diagnostic observations; conflicting_date_keys identifies unresolved dates. Run lengths use observed company-calendar sessions and include absent sessions as unavailable. Missing-price runs refer to missing parsed closes; negative/zero/nonfinite prices are invalid separately.",
        "## Prices, stale observations and discontinuities",
        table(["Diagnostic", "Rows", "Share of valid positive prices"], [
            ["Valid price with explicit zero volume", t['valid_price_zero_volume_rows'], pct(t['valid_price_zero_volume_rows'],valid)],
            ["Valid price with missing volume", t['valid_price_missing_volume_rows'], pct(t['valid_price_missing_volume_rows'],valid)],
            ["Potential stale price", t['potential_stale_price'], pct(t['potential_stale_price'],valid)],
            ["Positive prices in constant runs >=20 sessions", t['constant_price_run'], pct(t['constant_price_run'],valid)],
            ["Price changes with current zero volume", t['price_change_zero_volume'], pct(t['price_change_zero_volume'],valid)],
        ]),
        f"Negative prices: {t['negative_price']}; zero prices: {t['zero_price']}; negative volumes: {t['negative_volume']}; negative trade counts: {t['negative_trade_count']}; nonfinite prices: {t['nonfinite_price']}; numeric parse-issue rows: {t['numeric_parse_issue']}. Fractional volumes/trade counts: {t['fractional_volume']} / {t['fractional_trade_count']}. Maximum finite volume / trade count: {g['max_reported_volume']} / {g['max_reported_trade_count']}. Observed counts fit Int64 without rounding; recommend that type for curated counts with explicit future integer/range checks.",
        f"There are {s['fractional_close_observations']:,} non-integer closing values across {s['fractional_close_instruments']} instruments; see fractional_close_instruments.csv. This is a reason to preserve Float64 values and verify field/unit/adjustment definitions, not evidence of a particular adjustment basis.",
        f"There are {t['adjacent_price_returns']:,} diagnostic adjacent-session raw price returns, including {t['unchanged_adjacent_price_pairs']:,} unchanged-price pairs ({pct(t['unchanged_adjacent_price_pairs'],t['adjacent_price_returns'])}). An unchanged close is an observed equality, not proof of a genuine zero economic return. No return bridges a missing/invalid previous close or absent calendar session.",
        "A potential-stale flag means an unchanged adjacent valid price with current volume missing/nonpositive, or a constant-price run of at least 20 sessions with current volume missing/nonpositive. Constant prices accompanied by positive volume are reported separately, not automatically called stale. These are diagnostic flags, not corrections or exclusions. Full-period constant-run lengths are descriptive; any future as-of flag must use only trailing information.",
        table(["Absolute raw price-return threshold (strict >)", "Flagged adjacent returns"], [[f"{v}%",t[f'abs_return_gt_{v}pct']] for v in (10,20,30,50,100)]),
        f"{t['round_factor_corporate_action_candidate']:,} extreme returns are within 2% of a round split/consolidation factor. These require corporate-action records; ratios alone cannot distinguish splits, rights issues, distributions, ticker reuse or errors. suspicious_prices.csv retains source row references and original reported values for all diagnostics. Nothing is clipped, winsorised, filled or adjusted.",
        table(["Instrument", "Date", "Previous close", "Close", "Diagnostic raw change", "Volume"],
              [[r['instrument_id'],r['date'],r['previous_close_raw'],r['close_raw'],f"{r['diagnostic_price_return']*100:,.2f}%",r['volume']] for r in s['extreme_examples']]),
        "## Market-index validation",
        table(["Check", "Result"], [[k,m.get(k)] for k in ("instrument_ids","names","rows","frequency","start","end","unique_dates","calendar_month_ends","weekend_dates","missing_levels","invalid_levels","duplicate_dates","company_date_matches","company_dates_missing_from_index","missing_company_dates","index_dates_outside_company_calendar","min_level","max_level","daily_frequency_validated","calendar_complete","daily_benchmark_validated","return_variant")]),
        benchmark_layout,
        "The [JSE identifies J203 as All Share](https://www.jse.co.za/all-share-j203). The [JSE index data documentation](https://www.jse.co.za/market-data/our-market-data-products/index-market-data) distinguishes capital and total-return values, and [FTSE Russell's factsheet](https://research.ftserussell.com/Analytics/FactSheets/temp/4109f0b8-bb0e-4645-b73f-66ee5aa8d484.pdf) says the index family is available under both methodologies. The workbook contains no price-versus-total-return metadata. Its exact IRESS return variant remains unverified; do not infer dividend adjustment from the index name. Capture the IRESS field/series definition before deciding the return basis.",
        "See [market_index_validation.md](market_index_validation.md), market_calendar_alignment.csv and market_event_coverage.csv for the benchmark-only handover and exact window checks.",
        table(["Event date","Available market estimation returns / 221","Available market -10:+10 returns / 21","All required market closes present"],
              [[r['event_date'],r['available_estimation_returns'],r['available_visualisation_returns'],r['all_required_benchmark_sessions_present']] for r in s['market_event_coverage']]),
        "## Exploratory coverage around policy events",
        "Near means -10 through +10 company-calendar sessions, inclusive. Event day is the first available session on/after the provisional date. Estimation is -250 through -30 inclusive: 221 return dates, requiring the close at -251. A usable price-only observation requires two consecutive finite positive closes. The liquid definition requires positive reported volume at both endpoints. Full-window completeness requires every diagnostic return in that window. No threshold below is a final inclusion rule.",
        table(["Date","Event","Any near price","Near price + volume","Est >=150","Est >=180","Est >=200","Est180 + full -10:+10","Same, both endpoints trade"],event_rows),
        "The final two columns combine estimation coverage and full -10:+10 return coverage. Both-endpoint volume can substantially reduce apparent coverage; current-endpoint-only counts are also retained. A price-only count can include stale values and unresolved corporate actions. All counts are instruments, not verified firms. event_coverage.csv includes separate benchmark-paired counts, requiring the observed market close at both return endpoints; an unrelated full-period gap does not invalidate complete event windows.",
        table(["Date","Return definition","[0,+1]","[-1,+3]","[0,+5]","[-10,-1]","[-10,+10]","Est180 + all event windows"],[[r['event_date'],r['definition'],r['complete_event_0_1'],r['complete_event_m1_3'],r['complete_event_0_5'],r['complete_anticipation_m10_m1'],r['complete_caar_m10_10'],r['est180_and_all_event_windows']] for r in events]),
        "event_coverage.csv additionally reports all three estimation thresholds under all three return definitions. event_instrument_coverage.csv makes every count reproducible at instrument/event level. No CAR, CAAR, regression or policy-effect estimates are produced.",
        "## Recommended processing specification and review decisions",
        "See [processing_specification.md](processing_specification.md) for exact proposed types and metadata design. Keep every raw source row in intermediate Parquet. Recommend retaining all rows initially in the curated source table; optionally store entirely blank placeholder rows separately after approval, with exact key/source lineage and reconciliation counts. Preserve rows where even one financial field is present, and preserve all suspicious observations with flags. Keep conflicting keys unresolved rather than choosing a value silently.",
        "Material decisions for review: (1) canonical identical-duplicate reduction and all-source lineage; (2) retention versus separate storage of fully blank placeholders; (3) trailing stale-price rules and thresholds; (4) security types/share classes and the future company mapping; (5) future event-specific liquidity/completeness requirements; (6) price-return versus total-return basis and verified corporate-action treatment. We recommend approving source preservation and diagnostics now, and deferring research eligibility until benchmark, identity and adjustment metadata are obtained.",
        "Required external data: a verified daily benchmark and exchange sessions; a dated screener identifier snapshot to reconcile omissions; IRESS field definitions for quote units and adjustments; corporate-action and identifier histories; ISIN/security type/share class mappings and verified listing/delisting/suspension histories; point-in-time sectors and company links; dated market capitalisation, financial statements/leverage and B-BBEE/EE exposure. Historical information needs effective dates and publication/availability dates so future information cannot enter earlier eligibility or characteristics. Delisted instruments in this export do not establish a survivorship-bias-free universe.",
        "## Reproducibility and limits",
        "Run `uv run python -m iress_data audit`, then `uv run python -m iress_data verify`. Use `--force` to stream the Excel files again. Paths and DuckDB memory are configurable. Each workbook is read with openpyxl read-only mode into 20,000-row Arrow chunks; SQL validation can spill to disk; Python diagnostics retain one instrument at a time. The original exports and Playwright exporter are unchanged. SHA-256 hashes bind sources, pipeline code, uv.lock, intermediate artifacts and reports; software versions are recorded. audit_summary.json is written last as the completion marker. A repeated run replaces report files and reuses only hash-verified intermediates.",
        "Company Parquet builds, event eligibility and statistical analysis are deferred for review. When daily benchmark values pass numerical/identity checks, its observed levels are written to data/processed/market_index.parquet with source-row lineage and explicit calendar-gap metadata. This does not resolve the index return variant. Quote units, corporate-action adjustment, permanent company identity, historical security types and universe completeness are not established by this audit.",
    ]
    # Useful concrete examples selected deterministically from the actual findings.
    examples = sorted((r for r in instruments if r["valid_price_observations"]),
                      key=lambda r: (-r["longest_constant_price_sessions"],r["instrument_id"]))[:10]
    sections.insert(sections.index("## Market-index validation"), table(
        ["Instrument", "Name", "Valid prices", "Positive-volume days", "Longest constant run"],
        [[r['instrument_id'],r['company_names'],r['valid_price_observations'],r['positive_volume_days'],r['longest_constant_price_sessions']] for r in examples]))
    zero_only = [r for r in instruments if not r['valid_price_observations'] and r['zero_price']]
    sections.insert(sections.index("## Market-index validation"), table(
        ["Instrument with zero closes but no positive closes", "Source name", "Zero-close rows"],
        [[r['instrument_id'],r['company_names'],r['zero_price']] for r in zero_only]))
    candidate_ids = {r['observed_instrument_id'] for r in s['manifest_missing_name_candidates']}
    candidates = [r for r in instruments if r['instrument_id'] in candidate_ids]
    sections.insert(sections.index("## Duplicates and identities"), table(
        ["Name-discrepancy candidate", "Source name", "Valid price observations", "Positive-volume observations"],
        [[r['instrument_id'],r['company_names'],r['valid_price_observations'],r['positive_volume_days']] for r in candidates]))
    same_name_ids = {ident for r in s['same_name_examples'] for ident in r['instrument_ids'].split(',')}
    identity_rows = [r for r in instruments if r['instrument_id'] in same_name_ids]
    sections.insert(sections.index("## Missingness and useful history"), table(
        ["Source name", "Instrument", "First positive close", "Last positive close", "Positive-volume days"],
        [[r['company_names'],r['instrument_id'],r['first_valid_price_date'],r['last_valid_price_date'],r['positive_volume_days']] for r in identity_rows]))
    (cfg.reports / "data_audit.md").write_text("\n\n".join(sections) + "\n")
    write_market_report(cfg, s, benchmark_status, benchmark_layout)
    write_specification(cfg)


def write_market_report(cfg: Config, s: dict[str, Any], status: str, layout: str) -> None:
    m = s['market_index']
    output = s.get('market_index_processed')
    text = ["# J203 benchmark validation", status, layout,
        table(["Check","Observed result"], [[key,m.get(key)] for key in (
            'instrument_ids','rows','start','end','frequency','missing_levels','invalid_levels',
            'duplicate_dates','company_date_matches','company_dates_missing_from_index',
            'missing_company_dates','index_dates_outside_company_calendar','daily_frequency_validated',
            'calendar_complete','return_variant','source_sha256')]),
        table(["Missing index date","Company instruments reporting valid prices","Company instruments reporting positive volume","Reported share volume"],
            [[r['date'],r['valid_price_observations'],r['positive_volume_instruments'],r['total_reported_volume']] for r in s['market_missing_session_activity']]),
        table(["Event date","Estimation market returns / 221","Visualisation market returns / 21","Required sessions complete"],
            [[r['event_date'],r['available_estimation_returns'],r['available_visualisation_returns'],r['all_required_benchmark_sessions_present']] for r in s['market_event_coverage']]),
        (f"Observed daily source dataset: `{output['path']}` ({output['rows']:,} rows), with `market_index.metadata.json` alongside it. "
         "Date is Date32; index ID/name and provenance are strings; close_raw is Float64; units and return_variant remain null. "
         "The row after a missing company session is flagged is_adjacent_to_previous_session=false. No synthetic row or value is inserted."
         if output else "A daily source dataset was not produced because the benchmark did not pass daily frequency/identity/value checks."),
        "market_calendar_alignment.csv lists every observed company or index date, with missing/invalid/duplicate status. "
        "market_event_coverage.csv checks all 221 estimation return dates and all 21 visualisation return dates, including the preceding closes required to form returns. "
        "event_coverage.csv reports actual company/market paired availability under all three liquidity definitions.",
        "To close a source gap, export the missing date(s) from IRESS and validate the resulting observations before a provenance-preserving merge. "
        "Do not infer an index level or treat a multi-session change as a daily return. Daily frequency and numerical validity do not verify price-versus-total-return methodology."]
    (cfg.reports/'market_index_validation.md').write_text('\n\n'.join(text)+'\n')


def write_specification(cfg: Config) -> None:
    (cfg.reports / "processing_specification.md").write_text(SPECIFICATION)


SPECIFICATION = """# Proposed processing and handover specification — awaiting review

The company curated build awaits review. Original licensed workbooks are preserved by the pipeline. The intermediate schema and observed daily benchmark dataset are implemented; company processed schemas below remain proposals.

## Implemented standardised intermediate records

Every nonblank source row is retained, including entirely blank financial placeholders and duplicates. Company fields are Date32 date, String instrument_id/company_name, Float64 close_raw/volume/number_of_trades, String source_file/source_sheet, Int16 source_batch, Int32 source_row, String parse_issues/unparsed_values. Null financial cells stay null. Invalid numerical tokens become null with the original token retained; nonfinite numeric values stay nonfinite and are flagged. Workbook-level source hashes, source types, input/Parquet row counts and Parquet hashes are in sibling JSON files. Benchmark rows use the same core schema with null source_batch; trade counts are retained when the six-column Flat Data Table provides them, otherwise null. The original workbook preserves any extra OHLC fields. Both the six-column and eight-column benchmark layouts are supported; format acceptance does not imply daily frequency. Dates/identifiers that cannot be interpreted stop ingestion of that workbook and are reported as failures. Identifiers and company names retain their source spelling.

## Proposed data/processed/prices_daily.parquet

Unique key: (instrument_id, date). Keep original instrument ID and each share class separate. Prefer one file initially; a dataset partitioned by year is possible later.

| Fields | Arrow types | Meaning/rule |
| --- | --- | --- |
| date | date32 | Observed source session; no generated observations |
| instrument_id, company_name | string | Original source identifier and name |
| ticker | string nullable | Parse only a verified `ticker:venue:type` structure; ticker is not permanent identity |
| close_raw | float64 nullable | Original numerical close; units and adjustment basis unverified |
| volume, number_of_trades | int64 nullable, proposed | All observed counts are integral and in range; block future fractional/out-of-range inputs rather than round; retain source Float64/token in intermediate |
| source_file, source_sheet | string | Canonical source location |
| source_batch, source_row | int16, int32 | Canonical batch and original Excel row |
| source_sha256 | string | Hash from workbook inventory (or join through source_file) |
| duplicate_copy_count | int32 | Number of original copies; all copies in lineage table |
| has_valid_price | bool | Finite and >0; does not imply active trading |
| has_positive_volume | bool | Finite volume >0 |
| is_zero_volume, is_missing_volume | bool | Explicit zero distinguished from null |
| is_empty_placeholder | bool | All three reported numerical fields null and no parse error |
| numeric_parse_issue, negative_price, zero_price, negative_volume, negative_trade_count | bool | Observation quality flags; no deletion |
| unchanged_adjacent_price | bool nullable | Equality with previous valid close on verified adjacent session |
| trailing_constant_price_sessions | int32 nullable | Uses only information available through current session |
| potential_stale_price | bool | Proposed trailing-only diagnostic; exact threshold needs review |
| extreme_price_change | bool nullable | Adjacent-session raw price change exceeds reviewed threshold; null if uncomputable |
| diagnostic_price_return | float64 nullable, optional | Explicitly raw/unadjusted diagnostic, not accepted economic return |
| previous_price_date, price_gap_sessions | date32 nullable, int32 nullable | Make return adjacency inspectable |
| quality_rule_version | string | Version binding flags to reviewed rules |

Do not include full-period constant-run length as an as-of characteristic. Phase 1 uses full-run lengths descriptively only. No future price/volume coverage may determine historical eligibility. Return flags cannot bridge missing sessions.

## Proposed data/processed/instruments.parquet

One row per original instrument_id (string primary key), with ticker (nullable string), company_name (source label; name variants in separate table), observed_price_start/end and observed_positive_volume_start/end (nullable date32), observation/valid-price/positive-volume counts (int64), valid_price_coverage_pct (float64, denominator explicitly calendar sessions), source_batches (list<int16>), source_files (list<string>). These are descriptive data-availability fields, never listing dates. verified_security_type, ISIN, listing_date, delisting_date and issuer_id remain null until sourced; prefer separate effective-dated metadata below. Preserve every extracted instrument, including empty histories.

## Implemented data/processed/market_index.parquet

Unique (index_id, date). All observed valid daily levels are preserved without adjustment; a missing session remains absent and is documented. The file is not generated for monthly, wrong-identity, duplicate-date or invalid-level inputs. Gap-free completeness is checked separately from daily validity. A sibling market_index.metadata.json binds the source/output hashes and missing session dates.

| Fields | Arrow types | Meaning |
| --- | --- | --- |
| date | date32 | Observed index date |
| index_id, index_name | string | Source mnemonic and name |
| close_raw | float64 nullable | Reported level; no adjustment or interpolation |
| source_file, source_sheet, source_sha256 | string | Original workbook reference/hash |
| source_row | int32 | Original Excel row |
| frequency | string | daily, after daily validation |
| return_variant, units | string nullable | Null until confirmed from provider definitions |
| has_valid_price | bool | Finite strictly positive level |
| previous_observed_date | date32 nullable | Previous source observation, which can precede a gap |
| is_adjacent_to_previous_session | bool | True only if consecutive on the full observed company-session calendar |
| calendar_complete | bool | Full-period coverage of the company-session calendar; descriptive, not eligibility |

market_calendar_alignment.csv retains the complete calendar comparison. market_event_coverage.csv checks market close availability for every proposed event window, including previous closes required for returns. A full-period gap outside all event windows does not invalidate complete market-paired windows. Never bridge a missing session to create a daily return. J203 identity is supported by JSE documentation; exact IRESS price/total-return variant still requires confirmation. Any superseded monthly observations remain historical intermediate evidence, not daily data.

## Provenance and future metadata

| Dataset / key | Proposed fields |
| --- | --- |
| sources / source_id | file_name, SHA-256, provider, extraction timestamp if known, requested start/end, frequency, field definitions, units, adjustment basis, licence notes; use null for unknown extraction time |
| observation_lineage / instrument_id,date,source_id,source_sheet,source_row | canonical source reference, original copies, identical/conflict status; retained placeholder keys if stored separately |
| instrument_identifiers / instrument_id,identifier_type,value,valid_from | valid_to (exclusive), source_id, published_at, available_at; mnemonic/ISIN/ticker histories |
| instrument_issuer_links / instrument_id,issuer_id,valid_from | valid_to, relationship_type, share_class, source_id, published_at, available_at |
| listing_history / instrument_id,exchange,valid_from | valid_to, status, actual_listing_date, actual_delisting_date, source_id, published_at, available_at |
| sector_history / issuer_id,scheme,valid_from | valid_to, sector_code/name, classification_version, source_id, published_at, available_at |
| corporate_actions / action_id | instrument_id, action_type, announcement_date, ex_date, effective_date, ratio/cash amount/currency, source_id, published_at, available_at |
| financial_characteristics / issuer_id,metric,period_end,source_id | value, units, currency, consolidation_basis, statement_vintage, published_at, available_at |
| policy_exposure / issuer_id,metric,valid_from,source_id | valid_to, value, definition, assessment_period, published_at, available_at |
| market_calendar / exchange,date | is_session, session_open/close, timezone, source_id, verification status |
| instrument_name_history / instrument_id,valid_from,source_id | valid_to, company_name, published_at, available_at |

Effective date and the date information became publicly available serve different purposes. Preserve both, reject overlapping effective intervals where uniqueness is required, and use as-of joins constrained by available_at. Keep revised financial statement vintages. Do not backfill historical sectors/exposures from current labels. Source coverage dates are not a substitute for verified listing histories.

## Proposed transformation policies requiring review

1. Identical copies: choose lexicographically first filename, sheet, then lowest source row; retain every source reference. Conflicts: fail the build pending a documented explicit override, not an arbitrary winner.
2. Placeholder policy: initially retain every key. If size/usability warrants separation, move only rows where all financial fields are missing and no parse issue exists to an intermediate placeholder ledger; reconcile row counts and permit exact reconstruction. Never remove an entire instrument from the master merely for being empty.
3. Price/volume anomalies: preserve original values and set quality flags. No forward-fill, interpolation, winsorisation, unit conversion, dividend/split adjustment or zero-volume exclusion without an independently justified policy.
4. Stale definitions must be trailing-only for future event-date use; compare thresholds and definitions before research inclusion. Diagnostic thresholds are not eligibility.
5. Universe restrictions, firm mapping and event-specific estimation/liquidity requirements belong in a later explicit sample-construction layer. Benchmark validation and corporate-action basis are prerequisites.

## Reading after the future build

R: `prices <- arrow::read_parquet("data/processed/prices_daily.parquet")`; use `arrow::open_dataset()` for a partitioned dataset. Date32 is a native date, not a locale-dependent string. The R arrow package is an additional researcher-side dependency.

Python: `import pyarrow.parquet as pq; prices = pq.read_table("data/processed/prices_daily.parquet")`. Query Parquet directly with DuckDB for large extracts. At Phase 1, use the corresponding per-source paths under data/intermediate; those files retain duplicates and placeholder rows and are not final research data.

Monique's handover must include data dictionary, source/hash inventory, observed coverage, known omissions, approved transformation rules/version, quality diagnostics, benchmark definitions, unresolved units/adjustments and external metadata needs. Do not claim a permanent company mapping, adjustment basis or survivorship-bias-free universe before verification.
"""
