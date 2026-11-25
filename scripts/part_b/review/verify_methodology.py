#!/usr/bin/env python3
"""Recalculate Part B results with Python's standard library, then compare R exports."""

import csv
import json
import re
from collections import defaultdict
from fractions import Fraction
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "data/part_b/processed"
OUTPUT = ROOT / "mon_thesis/outputs/part_b"
DIAGNOSTICS = OUTPUT / "diagnostics/independent_methodology"
BLACK = {"African", "Coloured", "Indian"}
LEVELS = {"Top management": "top_management", "Senior management": "senior_management"}
INDICATORS = {"Black": "black", "Black female": "black_female"}
RESULTS = {}


def rows(directory, name):
    with (directory / f"{name}.csv").open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def key(row, columns):
    return tuple("NA" if row[c] in (None, "") else str(row[c]) for c in columns)


def index(data, columns):
    result = {}
    for row in data:
        k = key(row, columns)
        assert k not in result, (columns, k)
        result[k] = row
    return result


def number(value):
    return None if value in ("", "NA", "-") else Fraction(value.rstrip("%").replace(",", "."))


def compare(name, expected, columns, tolerance=5e-9):
    actual = index(rows(OUTPUT / "tables", name), columns)
    expected = index(expected, columns)
    assert actual.keys() == expected.keys(), (name, actual.keys() ^ expected.keys())
    maximum = 0.0
    cells = 0
    for k, fields in expected.items():
        for col, value in fields.items():
            other = actual[k][col]
            if isinstance(value, bool):
                assert other == ("TRUE" if value else "FALSE"), (name, k, col, value, other)
            elif isinstance(value, (int, Fraction)):
                error = abs(float(value - number(other)))
                assert error <= tolerance, (name, k, col, value, other)
                maximum = max(maximum, error)
            elif value is None:
                assert other in ("", "NA"), (name, k, col, other)
            else:
                assert value == other, (name, k, col, value, other)
            cells += 1
    RESULTS[name] = {"rows": len(expected), "fields_compared": cells, "max_numeric_error": maximum}


def serial(value):
    return round(float(value), 12) if isinstance(value, Fraction) else value


def save(name, records):
    with (DIAGNOSTICS / f"{name}.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows({k: serial(v) for k, v in row.items()} for row in records)


def share(numerator, denominator):
    return Fraction(100 * numerator, denominator)


def differences(end, start):
    return None if start is None or end is None else end - start


def normalize_label(label):
    label = label.casefold().replace("&", "and").replace("premeditation", "remediation")
    return " ".join(re.findall(r"[a-z]+", label))


def cee_review(reference):
    aliases = {}
    for row in reference:
        for col in ("cee_2023_sector_original", "cee_2024_sector_original",
                    "final_2025_sector_original", "draft_2023_sector_original"):
            label = normalize_label(row[col])
            assert aliases.setdefault(label, row["sector_id"]) == row["sector_id"]
    classification = index(rows(SOURCE, "cee_sector_crosswalk"), ("reporting_year", "sector_original"))
    groups = defaultdict(list)
    mapping = {}
    for row in rows(SOURCE, "cee_management_representation_raw"):
        year = int(row["reporting_year"])
        assert row["reporting_population"] == "All reporting employers"
        assert row["occupational_level"] in LEVELS
        if row["geographic_scope"] == "National":
            sector = "National"
        elif year >= 2019:
            source_key = (str(year), row["sector_original"])
            assert classification[source_key]["classification_system"] == "CEE 18-sector system"
            sector = aliases[normalize_label(row["sector_original"])]
            mapping[(year, sector)] = dict(reporting_year=year, sector_id=sector,
                                          sector_original=row["sector_original"])
        else:
            continue
        groups[(year, sector, row["occupational_level"])].append(row)
    assert set(groups) == (set(product(range(2016, 2026), ["National"], LEVELS)) |
                           set(product(range(2019, 2026), [r["sector_id"] for r in reference], LEVELS)))
    compare("cee_sector_label_mapping", mapping.values(), ("reporting_year", "sector_id"))

    management = {}
    printed = {}
    proxy_counts = {}
    for (year, sector, level), cells in sorted(groups.items()):
        by_group = index(cells, ("population_group", "gender"))
        assert set(by_group) == set(product(BLACK | {"White", "Foreign national"}, ("Male", "Female")))
        counts = {k: int(r["employee_count"]) for k, r in by_group.items()}
        total = sum(counts.values())
        assert total > 0 and min(counts.values()) >= 0
        assert {int(r["total_employees"]) for r in cells} == {total}
        b_male = sum(counts[(group, "Male")] for group in BLACK)
        b_female = sum(counts[(group, "Female")] for group in BLACK)
        management[year, sector, level] = dict(
            total_managers=total, black_manager_count=b_male + b_female,
            black_female_manager_count=b_female,
            black_representation_pct=share(b_male + b_female, total),
            black_female_representation_pct=share(b_female, total))
        printed[year, sector, level] = {
            code: sum(number(r["published_representation_pct"]) for (group, gender), r in by_group.items()
                      if group in BLACK and (code == "black" or gender == "Female"))
            for code in INDICATORS.values()
        }
        if year in (2023, 2024) and sector != "National":
            exact_ref = next(r for r in reference if r["sector_id"] == sector)
            assert {r["sector_original"] for r in cells} == {exact_ref[f"cee_{year}_sector_original"]}
            f = b_female + counts["White", "Female"]
            proxy_counts[year, sector, LEVELS[level]] = (total, {"male": b_male, "female": f, "total": b_male + f})

    all_rows = [dict(reporting_year=y, geographic_scope="National" if s == "National" else "Sector",
                     sector_id=None if s == "National" else s, occupational_level=l, **v)
                for (y, s, l), v in management.items()]
    compare("cee_national_management", [{k: v for k, v in r.items() if k != "sector_id"}
                                        for r in all_rows if r["geographic_scope"] == "National"
                                        and r["reporting_year"] <= 2024],
            ("reporting_year", "occupational_level"))
    # National output does not carry a sector_id column.
    sector_keys = ("reporting_year", "sector_id", "occupational_level")
    compare("cee_sector_management", [r for r in all_rows if r["sector_id"] and r["reporting_year"] <= 2024],
            sector_keys)
    compare("cee_management_2025_separate_regime",
            [dict(r, comparability_flag="2025_reporting_regime_break") for r in all_rows if r["reporting_year"] == 2025],
            ("geographic_scope", "sector_id", "occupational_level"))

    # Original 17th CEE report, Tables 10 and 15, PDF pp. 30 and 35.
    # Rendered all-employees count row, order A/C/I/W men, A/C/I/W women, foreign-national men/women.
    original = {
        "Top management": (59695, (5867, 1924, 3895, 33192, 2705, 1030, 1395, 7673, 1704, 310)),
        "Senior management": (142863, (19893, 6657, 9865, 55710, 11150, 4210, 5076, 26073, 3220, 1009)),
    }
    endpoint_rows = []
    level_gaps = []
    sensitivity = []
    for sector, level, (indicator, code) in product(
            ["National"] + sorted(r["sector_id"] for r in reference), LEVELS, INDICATORS.items()):
        field = f"{code}_representation_pct"
        start = 2016 if sector == "National" else 2019
        base, end = (management[y, sector, level][field] for y in (start, 2024))
        record = dict(sector_id=sector, occupational_level=level, indicator=indicator, start_year=start,
                      end_year=2024, start_pct=base, end_pct=end, change_pp=end - base)
        endpoint_rows.append(record)
        if sector == "National":
            denominator, counts = original[level]
            assert sum(counts) == denominator
            numerator = sum(counts[4:7]) + (sum(counts[:3]) if code == "black" else 0)
            original_pct = share(numerator, denominator)
            sensitivity.append(dict(record, original_2016_total=denominator, original_2016_numerator=numerator,
                                    original_2016_pct=original_pct, change_from_original_2016_pp=end - original_pct,
                                    change_from_2017_pp=end - management[2017, sector, level][field],
                                    retrospective_printed_2016_pct=printed[2016, sector, level][code]))
        if level == "Senior management":
            for year in range(start, 2025):
                top, senior = (management[year, sector, l][field] for l in LEVELS)
                level_gaps.append(dict(reporting_year=year, sector_id=sector, indicator=indicator,
                                       top_pct=top, senior_pct=senior, senior_minus_top_pp=senior - top))
    for scope in ("national", "sector"):
        national = scope == "national"
        for name, records, fields in [
            ("management_change", endpoint_rows, ("occupational_level", "indicator")),
            ("management_level_gaps", level_gaps, ("reporting_year", "indicator"))
        ]:
            subset = [r.copy() for r in records if (r["sector_id"] == "National") == national]
            if national:
                for r in subset:
                    del r["sector_id"]
            compare(f"cee_{scope}_{name}", subset, fields if national else ("sector_id", *fields))

    composition = []
    sectors = [r["sector_id"] for r in reference]
    for level, (indicator, code) in product(LEVELS, INDICATORS.items()):
        nfield, pfield = f"{code}_manager_count", f"{code}_representation_pct"
        totals = {y: sum(management[y, s, level]["total_managers"] for s in sectors) for y in (2019, 2024)}
        pooled = {y: share(sum(management[y, s, level][nfield] for s in sectors), totals[y]) for y in totals}
        fixed_2024 = sum(management[2024, s, level][pfield] *
                         Fraction(management[2019, s, level]["total_managers"], totals[2019]) for s in sectors)
        national = {y: management[y, "National", level] for y in totals}
        composition.append(dict(level=level, indicator=indicator, sector_total_2019=totals[2019],
                                national_total_2019=national[2019]["total_managers"],
                                sector_total_2024=totals[2024], national_total_2024=national[2024]["total_managers"],
                                national_less_pooled_2019_pp=national[2019][pfield] - pooled[2019],
                                national_change_pp=national[2024][pfield] - national[2019][pfield],
                                sector_pooled_change_pp=pooled[2024] - pooled[2019],
                                sector_change_fixed_2019_weights_pp=fixed_2024 - pooled[2019]))
    signs = []
    for level, indicator in product(LEVELS, INDICATORS):
        changes = [r for r in endpoint_rows if r["sector_id"] != "National" and
                   (r["occupational_level"], r["indicator"]) == (level, indicator)]
        signs.append(dict(level=level, indicator=indicator, positive=sum(r["change_pp"] > 0 for r in changes),
                          negative=[r["sector_id"] for r in changes if r["change_pp"] < 0],
                          zero=sum(r["change_pp"] == 0 for r in changes),
                          largest_gain=max(changes, key=lambda r: r["change_pp"])))
    print_deltas = sorted(
        [dict(year=y, sector=s, level=l, measure=code,
              count_less_printed_pp=management[y, s, l][f"{code}_representation_pct"] - value)
         for (y, s, l), profile in printed.items() if y == 2024 for code, value in profile.items()],
        key=lambda r: abs(r["count_less_printed_pp"]), reverse=True)
    coverage_rows = rows(SOURCE, "cee_reporting_coverage")
    coverage = [dict(reporting_year=r["reporting_year"],
                     reports_received=int(r["reports_received"]), employees_covered=int(r["employees_covered"]))
                for r in coverage_rows if r["geographic_scope"] == "National"]
    compare("cee_national_reporting_coverage", coverage, ("reporting_year",))
    coverage_2023_sum = sum(int(r["employees_covered"]) for r in coverage_rows
                            if (r["reporting_year"], r["geographic_scope"]) == ("2023", "Sector"))
    eap = defaultdict(lambda: {"black_eap_pct": 0, "black_female_eap_pct": 0})
    for r in rows(SOURCE, "cee_eap_benchmarks"):
        assert r["benchmark_year"] == r["reporting_year"] and r["benchmark_quarter"] == "3"
        if r["population_group"] in BLACK:
            eap[r["reporting_year"]]["black_eap_pct"] += number(r["representation_pct"])
            if r["gender"] == "Female":
                eap[r["reporting_year"]]["black_female_eap_pct"] += number(r["representation_pct"])
    compare("cee_national_eap", [dict(reporting_year=y, benchmark_year=y, benchmark_quarter=3, **v)
                                 for y, v in eap.items()], ("reporting_year",))
    save("cee_endpoint_changes", endpoint_rows)
    return proxy_counts, dict(original_2016_sensitivity=sensitivity, sector_weight_sensitivity=composition,
                              sector_directions=signs, largest_2024_printed_share_differences=print_deltas[:4],
                              eap_2024=eap["2024"], sector_employee_sum_2023=coverage_2023_sum,
                              coverage=coverage)


def ownership_review():
    keys = ("reporting_year", "sector_original", "ownership_measure")
    source = index([r for r in rows(SOURCE, "bbbee_ownership")
                    if (r["series_id"], r["entity_size"]) == ("retro_2026", "All")], keys)
    assert all(not (r["numerator"] or r["denominator"] or r["indicator_sample_n"]) for r in source.values())
    values = {k: number(r["published_value_original"]) for k, r in source.items()}
    assert all(value == number(source[k]["ownership_pct"]) for k, value in values.items())
    assert [k for k, v in values.items() if v is None] == [("2013", "Property", "black_female_economic_interest")]

    coverage = [r for r in rows(SOURCE, "bbbee_reporting_coverage") if r["series_id"] == "retro_2026"]
    sizes = index([r for r in coverage if r["coverage_measure"] == "sample_entries_by_enterprise_size"],
                  ("reporting_year", "entity_size"))
    codes = index([r for r in coverage if r["coverage_measure"] == "sample_entries_by_sector"],
                  ("reporting_year", "sector_original"))

    pairs = []
    masks = set()
    flagged_female = set()
    for (y, s, m), overall in sorted(values.items()):
        if m not in {"black_economic_interest", "black_voting_rights"}:
            continue
        female_measure = m.replace("black_", "black_female_", 1)
        female_key = (y, s, female_measure)
        female = values[female_key]
        if female is not None and female > overall:
            in_period = 2016 <= int(y) <= 2023
            pairs.append(dict(reporting_year=y, sector_original=s, ownership_measure=m,
                              overall_pct=overall, female_pct=female, female_measure=female_measure,
                              in_primary_period=in_period))
            flagged_female.add(female_key)
            if in_period:
                masks.update(((y, s, m), female_key))
    assert flagged_female == {k for k, r in source.items()
                              if "female_average_exceeds_overall_unresolved" in r["quality_flag"]}
    assert len(pairs) == 10 and len(masks) == 16
    compare("bbbee_ownership_anomaly_pairs", pairs, keys)
    primary = {k: v for k, v in values.items() if 2016 <= int(k[0]) <= 2023}
    annual, sensitivity = [], []
    for (y, s, m), value in sorted(primary.items()):
        count = int(codes[y, "Grand Total" if s == "National" else s]["sample_count"])
        assert count == int(source[y, s, m]["contextual_sample_n"])
        fields = dict(reporting_year=y, sector_original=s, ownership_measure=m,
                      series_id="retro_2026", contextual_sample_n=count)
        annual.append(dict(fields, ownership_pct=value, entity_size="All"))
        sensitivity.append(dict(fields, published_pct=value, excluded_as_anomaly_pair=(y, s, m) in masks,
                                pair_excluded_pct=None if (y, s, m) in masks else value))
    compare("bbbee_ownership_annual", annual, keys)
    compare("bbbee_ownership_annual_sensitivity", sensitivity, keys)

    endpoints = []
    for sector, measure in sorted({(s, m) for _, s, m in primary}):
        published = {int(y): v for (y, s, m), v in primary.items() if (s, m) == (sector, measure)}
        retained = {y: v for y, v in published.items() if (str(y), sector, measure) not in masks}
        start, end = (published.get(y) for y in (2016, 2023))
        retained_start, retained_end = (retained.get(y) for y in (2016, 2023))
        code = "Grand Total" if sector == "National" else sector
        endpoints.append(dict(
            sector_original=sector, ownership_measure=measure, start_year=2016, end_year=2023,
            start_pct=start, end_pct=end, start_pct_pair_excluded=retained_start, end_pct_pair_excluded=retained_end,
            start_context_n=int(codes["2016", code]["sample_count"]) if start is not None else None,
            end_context_n=int(codes["2023", code]["sample_count"]) if end is not None else None,
            change_pp=differences(end, start), change_pp_pair_excluded=differences(retained_end, retained_start),
            years_observed=len(published), years_excluded=len(published) - len(retained),
            first_observed_year=min(published), first_observed_pct=published[min(published)],
            first_retained_year=min(retained), first_retained_pct=retained[min(retained)],
            change_from_first_observed_pp=differences(end, published[min(published)]),
            change_from_first_retained_pp=differences(retained_end, retained[min(retained)])))
    compare("bbbee_ownership_change_and_sensitivity", endpoints, keys[1:])
    directions = []
    for measure in sorted({r["ownership_measure"] for r in endpoints}):
        sector_values = [r for r in endpoints if r["sector_original"] != "National" and r["ownership_measure"] == measure]
        baseline = [r["change_pp"] for r in sector_values if r["change_pp"] is not None]
        excluded = [r for r in sector_values if r["change_pp_pair_excluded"] is not None]
        assert all(r["change_pp"] == r["change_pp_pair_excluded"] for r in excluded)
        directions.append(dict(ownership_measure=measure, published_sectors=len(baseline),
                               published_increases=sum(x > 0 for x in baseline), pair_excluded_sectors=len(excluded),
                               pair_excluded_increases=sum(r["change_pp_pair_excluded"] > 0 for r in excluded),
                               common_endpoint_increases=sum(r["change_pp"] > 0 for r in excluded)))
    compare("bbbee_ownership_sector_direction_sensitivity", directions, ("ownership_measure",))
    economic_interest = [r for r in endpoints if r["sector_original"] != "National" and
                         r["ownership_measure"] == "black_economic_interest" and
                         r["change_pp_pair_excluded"] is not None]
    screen = {threshold: [r["sector_original"] for r in economic_interest
                          if min(r["start_context_n"], r["end_context_n"]) >= threshold]
              for threshold in (0, 10, 20, 30, 32, 36, 50)}
    save("bbbee_ownership_endpoints", endpoints)
    return dict(anomaly_pairs=pairs, directions=directions, code_figure_context_count_sensitivity=screen,
                national_coverage={y: {size: int(sizes[y, size]["sample_count"])
                                       for size in ("EME", "QSE", "Large", "Unknown", "Grand Total")}
                                   for y in ("2016", "2023")})


def status_review():
    groups = defaultdict(dict)
    for row in rows(SOURCE, "bbbee_compliance_levels"):
        year = int(row["reporting_year"])
        if row["series_id"] == "retro_2026" and row["entity_size"] == "All" and 2016 <= year <= 2023:
            levels = groups[(year, row["sector_original"])]
            name = row["compliance_level"]
            assert name not in levels
            levels[name] = row
    known_levels = {f"Level {i}" for i in range(1, 9)} | {"Non-Compliant", "Grand Total"}
    totals, distributions, exclusions, summary, inferred_groups = [], [], [], [], []
    for (year, sector), levels in sorted(groups.items()):
        assert levels.keys() == known_levels
        counts = {k: number(row["published_count_original"]) for k, row in levels.items()}
        total = counts.pop("Grand Total")
        assert total is not None and total > 0
        count_sum = sum(v for v in counts.values() if v is not None)
        fields = dict(reporting_year=year, sector_original=sector, series_id="retro_2026", entity_size="All")
        if count_sum != total:
            assert all(not r["calculated_pct"] for r in levels.values())
            totals.append(dict(fields, published_total=total, sum_level_counts=count_sum))
            exclusions.append(dict(fields, analytical_value=None))
            continue
        for level, n in counts.items():
            reported = number(levels[level]["published_pct_original"])
            distributions.append(dict(fields, compliance_level=level, entity_count=n,
                                      published_pct=reported, valid_status_denominator=total,
                                      calculated_pct=None if n is None else 100 * n / total))
        top = {level: counts[level] for level in (f"Level {i}" for i in range(1, 5))}
        for level, n in top.items():
            if n is None:
                assert number(levels[level]["published_pct_original"]) == 0
                top[level] = 0
        if any(counts[level] is None for level in top):
            inferred_groups.append((year, sector))
        numerator = sum(top.values())
        summary.append(dict(fields, analytical_value=100 * numerator / total, numerator=numerator, denominator=total))
    keys = ("reporting_year", "sector_original")
    compare("bbbee_compliance_levels_valid", distributions, (*keys, "compliance_level"), tolerance=0.000051)
    compare("bbbee_compliance_levels_1_to_4", summary, keys, tolerance=0.000051)
    compare("bbbee_compliance_exclusions", exclusions, keys)
    return dict(invalid_distributions=totals, valid_count_dashes=sum(r["entity_count"] is None for r in distributions),
                levels_1_to_4_zero_inferences=inferred_groups,
                national_levels_1_to_4=[r for r in summary if r["sector_original"] == "National"],
                selected_2023_levels_1_to_4=[r for r in summary if r["reporting_year"] == 2023
                                            and r["sector_original"] in {"Construction", "Tourism"}])


def target_review(reference, proxy_counts):
    keys = ("sector_id", "occupational_level", "gender")
    target_rows = rows(SOURCE, "ee_sector_targets")
    draft = index([r for r in target_rows if (r["policy_version"], r["geographic_scope"], r["target_population"])
                   == ("draft_2023", "national", "black")], keys)
    final = index([r for r in target_rows if (r["policy_version"], r["geographic_scope"], r["target_population"])
                   == ("final_2025", "national", "designated_groups")], keys)
    baseline = index([r for r in rows(SOURCE, "ee_gazette_workforce_baseline_2022")
                      if (r["reporting_year"], r["population_group"]) == ("2022", "black")], keys)
    ref = {r["sector_id"]: r for r in reference}
    assert draft.keys() == baseline.keys() == final.keys() == set(product(ref, LEVELS.values(), ("total", "male", "female")))
    shortfalls = {}
    finals = {}
    for (sector, level, gender), row in draft.items():
        k = (sector, level, gender)
        base = baseline[k]
        assert all(row[col] == base[col] for col in ("source_id", "source_page_pdf", "source_page_printed", "sector_original"))
        assert row["source_id"] == "EE2023" and row["announcement_date"] == base["publication_date"] == "2023-05-12"
        assert row["sector_original"] == ref[sector]["draft_2023_sector_original"]
        assert base["reporting_population"] == "Workforce Profile 2022 (All employers)"
        target, observed = (number(r["published_value_original"]) for r in (row, base))
        assert target == number(row["target_pct"]) and observed == number(base["observed_pct"])
        fields = dict(zip(keys, k))
        shortfalls[k] = dict(fields, shortfall_pp=target - observed, target_pct=target, observed_pct=observed)
        f = final[k]
        assert f["sector_original"] == ref[sector]["final_2025_sector_original"]
        assert f["source_id"] == "EE2025" and f["announcement_date"] == "2025-04-15"
        target_final = number(f["published_value_original"])
        assert target_final == number(f["target_pct"])
        finals[k] = dict(fields, target_pct=target_final, target_population="designated_groups")
    for s, l in product(ref, LEVELS.values()):
        for records, columns in ((shortfalls, ("shortfall_pp", "target_pct", "observed_pct")), (finals, ("target_pct",))):
            for col in columns:
                assert records[s, l, "total"][col] == records[s, l, "male"][col] + records[s, l, "female"][col]
    extremes = []
    for level, gender in product(LEVELS.values(), ("total", "male", "female")):
        group = [r for r in shortfalls.values() if (r["occupational_level"], r["gender"]) == (level, gender)]
        gaps = [r["shortfall_pp"] for r in group]
        for r in group:
            r["shortfall_rank"] = 1 + sum(x > r["shortfall_pp"] for x in gaps)
        extrema = {label: [r["sector_id"] for r in group if r["shortfall_pp"] == value]
                   for label, value in (("min_sectors", min(gaps)), ("max_sectors", max(gaps)))}
        extremes.append(dict(level=level, gender=gender, min_pp=min(gaps), max_pp=max(gaps), **extrema,
                             positive=sum(x > 0 for x in gaps), zero=sum(x == 0 for x in gaps),
                             negative=sum(x < 0 for x in gaps)))
    proxy = []
    for (year, sector, level), (denominator, counts) in sorted(proxy_counts.items()):
        for gender, count in counts.items():
            record = finals[sector, level, gender]
            pct = share(count, denominator)
            timing = "Pre-announcement context" if year == 2023 else "Retrospective context"
            proxy.append(dict(record, reporting_year=year, total_managers=denominator, proxy_count=count,
                              proxy_pct=pct, difference_from_cee_proxy_pp=record["target_pct"] - pct, workforce_timing=timing))
    compare("ee_draft_2023_target_shortfalls", shortfalls.values(), keys)
    compare("ee_final_2025_targets", finals.values(), keys)
    compare("ee_final_2025_cee_proxy_supplement", proxy, ("reporting_year", *keys))
    save("ee_draft_shortfalls", sorted(shortfalls.values(), key=lambda r: key(r, keys)))
    save("ee_final_proxy", proxy)
    return dict(draft_extremes=extremes, final_target_ranges={
        l: [fn(r["target_pct"] for r in finals.values() if (r["occupational_level"], r["gender"]) == (l, "total"))
            for fn in (min, max)] for l in LEVELS.values()
    })


def employment_review():
    totals, industry = [], []
    for row in rows(SOURCE, "statssa_sector_employment"):
        if row["geographic_scope"] == "national" and row["observation_quarter"] == "3":
            y = int(row["observation_year"])
            if 2016 <= y <= 2025:
                assert row["published_unit"] == "Thousand" and "Table B" in row["source_table_or_sheet"]
                n = int(row["published_employment_value"]) * 1000
                assert n == int(row["employment_persons"])
                entry = dict(observation_year=y, observation_period=f"{y}Q3", employment_persons=n,
                             publication_vintage=row["publication_vintage"], comparability_flag=row["comparability_flag"],
                             industry_standardised=row["industry_standardised"])
                if row["industry_standardised"] == "national_total":
                    totals.append(entry)
                else:
                    industry.append(entry)
    totals.sort(key=lambda r: r["observation_year"])
    prior = None
    for r in totals:
        current = r["employment_persons"]
        r["change_from_prior_q3_persons"] = differences(current, prior)
        prior = current
    compare("qlfs_q3_national_employment", totals, ("observation_period",))
    compare("qlfs_q3_industry_employment", industry, ("observation_period", "industry_standardised"))
    return [dict(r, published_total_less_listed_industries=r["employment_persons"] - sum(
        x["employment_persons"] for x in industry if x["observation_year"] == r["observation_year"])) for r in totals]


def main():
    DIAGNOSTICS.mkdir(parents=True, exist_ok=True)
    reference = rows(SOURCE, "ee_sector_reference")
    proxy_counts, cee = cee_review(reference)
    results = dict(cee=cee, bbbee_ownership=ownership_review(), bbbee_status=status_review(),
                   employment_equity=target_review(reference, proxy_counts), qlfs=employment_review(),
                   comparisons=RESULTS)
    (DIAGNOSTICS / "verification.json").write_text(json.dumps(results, indent=2, default=serial) + "\n")
    print(f"Reconciled {sum(r['rows'] for r in RESULTS.values()):,} keyed rows across {len(RESULTS)} R tables.")


if __name__ == "__main__":
    main()
