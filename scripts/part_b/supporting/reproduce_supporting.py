"""Reproduce the bounded Employment Equity and QLFS supporting collection."""
import csv
import hashlib
import re
import subprocess
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).parent
DATA = Path("data/part_b")
DOCS = Path("docs/part_b")
OUT = DATA / "processed"
GENDERS = ("male", "female", "total")
LEVELS = ("top_management", "senior_management")
VALIDATION = []


def records(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def check(dataset, source, name, expected, actual, notes="", status=None):
    status = status or ("pass" if expected == actual else "fail")
    VALIDATION.append(dict(dataset=dataset, source=source, check=name,
                           expected_result=expected, actual_result=actual,
                           status=status, discrepancy_or_explanation=notes))


def text_pages(path, start=None, end=None, mode="-layout"):
    pages = [] if start is None else ["-f", str(start), "-l", str(end or start)]
    return subprocess.check_output(["pdftotext", *pages, mode, str(path), "-"], text=True)


def pct(value):
    return Decimal(value.removesuffix("%").replace(",", "."))


def read_draft():
    source = DATA / "raw/gazettes/48589gon3407.pdf"
    rows = {}
    pages = text_pages(source).split("\f")
    review = {int(r["pdf_page"]): r for r in records(HERE / "draft_2023_verification.csv")}
    for line in (HERE / "draft_2023_transcription.txt").read_text().splitlines():
        if line.startswith("#"):
            continue
        page, sector_id, sector, *groups = line.split("|")
        page = int(page)
        printed = page + 18
        assert re.search(rf"^\s*{printed}\s+No\. 48589", pages[page - 1])
        verified = review[page]
        keys = ("national_top", "national_senior", "workforce_top", "workforce_senior")
        for key, group in zip(keys, groups, strict=True):
            dataset = ("ee_sector_targets" if key.startswith("national")
                       else "ee_gazette_workforce_baseline_2022")
            values = group.split()
            independent = verified[key].split()
            assert len(values) == len(independent) == 3
            for gender, value, reference in zip(GENDERS, values, independent):
                check(dataset, "EE2023", f"PDF {page}, {key}, {gender}", reference,
                      value, verified["notes"])
        rows[sector_id] = (sector, page, printed, groups)
    assert len(rows) == len(review) == 18
    return rows


def make_ee(draft, final):
    targets = []
    baseline = []
    for version, status, date, gazette, notice, population, source_id, sectors in (
        ("draft_2023", "draft", "2023-05-12", 48589, 3407, "black", "EE2023", draft),
        ("final_2025", "final", "2025-04-15", 52514, 6124, "designated_groups", "EE2025", final),
    ):
        for sector_id, (sector, page, printed, groups) in sectors.items():
            for index, group in enumerate(groups):
                level = LEVELS[index % 2]
                workforce = index >= 2
                name = "ee_gazette_workforce_baseline_2022" if workforce else "ee_sector_targets"
                male, female, total = map(pct, group.split())
                difference = total - male - female
                flag = ("ok" if not difference else "published_rounding_difference"
                        if abs(difference) <= Decimal("0.1") else "published_total_discrepancy")
                check(name, source_id, f"{sector_id}, {level}: total minus male and female", 0,
                      difference, "Published percentages retained." if difference else "",
                      "source_note" if difference else "pass")
                for gender, value in zip(GENDERS, group.split(), strict=True):
                    citation = dict(published_value_original=value, source_id=source_id,
                                    source_page_pdf=page, source_page_printed=printed,
                                    quality_flag=flag if gender == "total" else "ok")
                    if workforce:
                        baseline.append(dict(reporting_year=2022, publication_date=date,
                                             sector_original=sector, sector_id=sector_id,
                                             occupational_level=level, population_group="black",
                                             gender=gender, observed_pct=pct(value),
                                             reporting_population="Workforce Profile 2022 (All employers)",
                                             **citation))
                    else:
                        targets.append(dict(target_id=f"{version}_{sector_id}_{level}_{gender}",
                                            policy_version=version, policy_status_at_publication=status,
                                            announcement_date=date, gazette_number=gazette,
                                            notice_number=notice, target_horizon_years=5,
                                            sector_original=sector, sector_id=sector_id,
                                            geographic_scope="national", occupational_level=level,
                                            target_population=population, gender=gender,
                                            target_pct=pct(value), **citation))
    return targets, baseline


def read_final():
    path = DATA / "raw/gazettes/52514gon6124.pdf"
    official_list = re.findall(r"^\s*1\.\d+\.\s+([^\n]+)", text_pages(path, 2), re.M)
    review = []
    for line in (HERE / "final_2025_verification.txt").read_text().splitlines():
        if not line.startswith("#"):
            page, sector_id, heading, *groups = line.split("|")
            review.append((int(page), sector_id, heading, groups))
    assert len(official_list) == len(review) == 18
    ids = {heading: sector_id for _, sector_id, heading, _ in review}
    table = {}
    for page, content in enumerate(text_pages(path, 4, 8).split("\f")[:5], start=4):
        printed = page + 2
        assert re.search(rf"(?:{printed}\s+No\. 52514|No\. 52514\s+{printed})", content)
        prefix, subsequent = content.split("DESIGNATED GROUPS", maxsplit=1)
        headers = re.findall(r"(?<![\w-])(\d{1,2})\.\s+[A-Z]", prefix)
        expected_columns = subsequent.splitlines()[0].count("DESIGNATED GROUPS") + 1
        assert len(headers) == expected_columns
        selected = subsequent.split("Professionally", maxsplit=1)[0]
        extracts = re.findall(r"\b(Male|Female|Total)\s+((?:\d+\.\d+%[ \t]*)+)", selected)[:6]
        assert [gender.lower() for gender, _ in extracts] == list(GENDERS) * 2
        assert all(len(values.split()) == expected_columns for _, values in extracts)
        for number, values in zip(headers, zip(*(v.split() for _, v in extracts)), strict=True):
            heading = official_list[int(number) - 1].upper()
            sector_id = ids[heading]
            table[sector_id] = (heading, page, printed,
                                (" ".join(values[:3]), " ".join(values[3:])))
    assert len(table) == 18
    for page, sector_id, heading, groups in review:
        actual_heading, actual_page, _, actual_groups = table[sector_id]
        assert (heading, page) == (actual_heading, actual_page)
        for level, actual, expected in zip(LEVELS, actual_groups, groups, strict=True):
            for gender, value, reference in zip(GENDERS, actual.split(), expected.split(), strict=True):
                check("ee_sector_targets", "EE2025", f"{sector_id}, {level}, {gender}",
                      reference, value, f"PDF {page}; compared Poppler extraction with visual transcription.")
    return table


def label_key(label):
    label = label.upper().replace("&", "AND").replace("TRANSPORTATION", "TRANSPORT")
    return re.sub(r"[^A-Z0-9 ]", "", label)


def make_sector_reference(draft, final):
    raw = records(OUT / "cee_management_representation_raw.csv")
    crosswalk = records(OUT / "cee_sector_crosswalk.csv")
    cee_labels = {
        year: {label_key(r["sector_original"]): r["sector_original"] for r in crosswalk
               if r["reporting_year"] == year}
        for year in ("2023", "2024")
    }
    assert len(cee_labels["2023"]) == len(cee_labels["2024"]) == 18
    assert set(draft) == set(final)
    rows = []
    for sector_id, (final_label, _, _, _) in final.items():
        draft_label = draft[sector_id][0]
        assert label_key(draft_label) == label_key(final_label)
        key = label_key(final_label)
        evidence = "Gazette 48589 p. 20; Gazette 52514 p. 4; EEA17 pp. 98–101; both CEE Appendix C labels."
        notes = ""
        status = "matched_label"
        if sector_id == "trade_repair":
            key = "WHOLESALE TRADE COMMERCIAL AGENTS AND ALLIED SERVICES"
            evidence = ("EEA17 p. 101; CEE 24th PDF pp. 34, 39, 99; CEE 25th PDF pp. 35, 40, 98. "
                        "Tables 7 and 10 and Appendix C have identical 11-cell published percentage "
                        "vectors within each year and level.")
            notes = "CEE Appendix C uses the commercial agents label; the body tables use the broader trade and repair label."
            status = "matched_within_report_evidence"
            check_trade_alias(cee_labels["2023"][key], raw)
        elif sector_id in {"agriculture", "transport_storage", "electricity_gas", "public_administration"}:
            notes = "Source spelling or punctuation varies."
        rows.append(dict(sector_id=sector_id, sector_name=final_label, draft_2023_sector_original=draft_label,
                         final_2025_sector_original=final_label,
                         cee_2023_sector_original=cee_labels["2023"][key],
                         cee_2024_sector_original=cee_labels["2024"][key],
                         mapping_status=status, mapping_evidence=evidence, notes=notes))
    for field in ("draft_2023_sector_original", "final_2025_sector_original",
                  "cee_2023_sector_original", "cee_2024_sector_original"):
        check("ee_sector_reference", "EE2023; EE2025; EEADMIN2025; CEE24; CEE25", field,
              18, len({r[field] for r in rows}))
    check_cee_counts(raw, rows)
    return rows


def check_trade_alias(label, cee):
    for year, report, pages in (("2023", 24, (34, 39)), ("2024", 25, (35, 40))):
        path = DATA / f"raw/cee/cee_{report}th_annual_report.pdf"
        for level, page in zip(("Top management", "Senior management"), pages, strict=True):
            table = text_pages(path, page)
            row = re.search(r"^.*Wholesale and\s+((?:\d+[,.]\d+%[ \t]*){11})", table, re.M)
            if row is None:
                # The 25th report's body table centres numbers next to the wrapped label.
                row = re.search(r"retail trade; repair of\s+((?:\d+[,.]\d+%[ \t]*){11})", table)
            assert row is not None, (year, level, page)
            body = tuple(map(pct, row[1].split()))
            appendix = tuple(Decimal(r["published_representation_pct"]) for r in cee
                             if r["reporting_year"] == year and r["sector_original"] == label
                             and r["occupational_level"] == level and r["geographic_scope"] == "Sector")
            appendix += (Decimal("100.0"),)
            check("ee_sector_reference", f"CEE{report}", f"trade label evidence, {level}",
                  body, appendix, f"Body PDF page {page} compared with reviewed Appendix C percentages.")


def check_cee_counts(cee, reference):
    population = {"African", "Coloured", "Indian", "White", "Foreign national"}
    expected = {(group, gender) for group in population for gender in ("Male", "Female")}
    for year, report in (("2023", 24), ("2024", 25)):
        field = f"cee_{year}_sector_original"
        data = [r for r in cee if r["reporting_year"] == year and r["geographic_scope"] == "Sector"
                and r["reporting_population"] == "All reporting employers"]
        reconciled = 0
        for sector in reference:
            for level in ("Top management", "Senior management"):
                cells = [r for r in data if r["sector_original"] == sector[field]
                         and r["occupational_level"] == level]
                if len(cells) == 10 and {(r["population_group"], r["gender"]) for r in cells} == expected:
                    counts = [int(r["employee_count"]) for r in cells]
                    denominators = {int(r["total_employees"]) for r in cells}
                    reconciled += min(counts) >= 0 and sum(counts) > 0 and denominators == {sum(counts)}
        check("ee_sector_reference", f"CEE{report}", f"{year} proxy input completeness", 36, reconciled,
              "Ten count cells reconcile to one inclusive occupational-level total in each sector-level group.")


QLFS_RELEASES = {
    2017: ("2017-10-31", 7, 2),
    2019: ("2019-10-29", 7, 2),
    2021: ("2021-11-30", 8, 3),
    2023: ("2023-11-14", 7, 2),
    2025: ("2025-11-11", 8, 3),
}
INDUSTRIES = {
    "Total*": "national_total", "Agriculture": "agriculture", "Mining": "mining",
    "Manufacturing": "manufacturing", "Utilities": "utilities", "Construction": "construction",
    "Trade": "trade", "Transport": "transport", "Finance": "finance",
    "Community and social services": "community_social_services",
    "Private households": "private_households",
}
COVERAGE = "Employed persons aged 15–64 in the QLFS household survey"


def read_qlfs():
    name = "statssa_sector_employment"
    review = {}
    for line in (HERE / "qlfs_table_b_verification.txt").read_text().splitlines():
        if not line.startswith("#"):
            year, *values = map(int, line.split("|"))
            review[year] = dict(zip(INDUSTRIES.values(), values, strict=True))
    rows = []
    for vintage, (date, pdf_page, printed) in QLFS_RELEASES.items():
        source_id = f"QLFS{vintage}Q3"
        path = DATA / f"raw/statssa/P02113rdQuarter{vintage}.pdf"
        content = text_pages(path, pdf_page)
        assert re.search(rf"STATISTICS SOUTH AFRICA\s+{printed}\s+P0211", content)
        assert re.search(rf"Quarterly Labour Force Survey, Quarter 3[:,]?\s+{vintage}", content)
        before_notes = content.split("Table B: Employment by industry", 1)[1].split("*Note:", 1)[0]
        header, values = re.split(r"^\s*(?=Total\*)", before_notes, maxsplit=1, flags=re.M)
        assert re.search(r"Jul-Sep\s+Apr-Jun\s+Jul-Sep", header)
        assert re.search(rf"{vintage - 1}\s+{vintage}\s+{vintage}", header)
        assert "Thousand" in header
        labels = {("Finance and other business services" if vintage == 2017 and key == "Finance" else key): val
                  for key, val in INDUSTRIES.items()}
        estimates = {}
        for original, industry in labels.items():
            match = re.search(rf"^\s*{re.escape(original)}[ \t]{{2,}}([^\n]+)", values, re.M)
            assert match is not None, (vintage, original)
            cells = re.split(r"\s{2,}", match[1].strip())
            assert len(cells) == 7
            estimates[industry] = (original, [int(c.replace(" ", "")) for c in cells[:3]])
        for year, column in ((vintage - 1, 0), (vintage, 2)):
            for industry, (original, values) in estimates.items():
                value = values[column]
                location = f"printed {printed}; PDF {pdf_page}; Jul-Sep {year}"
                check(name, source_id, f"{year} Q3, {original}", review[year][industry], value,
                      f"{location}; rendered Table B checked against Poppler extraction.")
                if year in {2020, 2021}:
                    comparability = "mixed_vintage_pandemic_phone_collection"
                elif year == 2022:
                    comparability = "mixed_vintage_return_to_in_person_collection"
                elif year == 2025:
                    comparability = "mixed_vintage_2025_questionnaire_revision"
                else:
                    comparability = "mixed_publication_vintage"
                rows.append(dict(observation_year=year, observation_quarter=3,
                                 observation_period=f"{year}Q3", industry_original=original,
                                 industry_standardised=industry, geographic_scope="national",
                                 survey="QLFS", population_coverage=COVERAGE,
                                 published_employment_value=value, published_unit="Thousand",
                                 employment_persons=1000 * value, publication_date=date,
                                 publication_vintage=f"{vintage}Q3", source_id=source_id,
                                 source_table_or_sheet="Table B: Employment by industry",
                                 source_page_or_cell=location, quality_flag="ok",
                                 comparability_flag=comparability))
            total = estimates["national_total"][1][column]
            visible_sum = sum(v[1][column] for k, v in estimates.items() if k != "national_total")
            difference = total - visible_sum
            check(name, source_id, f"{year} Q3 total minus ten displayed industries",
                  "Published total retained", difference,
                  "Thousand persons. Total includes Other and displayed figures are rounded; no residual series.",
                  "source_note")
    return rows


def check_sources():
    source_ids = set()
    for row in records(DOCS / "supporting_source_inventory.csv"):
        source_id = row["source_id"]
        assert source_id not in source_ids
        source_ids.add(source_id)
        if row["local_path"]:
            path = Path(row["local_path"])
            with path.open("rb") as stream:
                fingerprint = hashlib.file_digest(stream, "sha256").hexdigest()
            check("source_inventory", source_id, "SHA-256", row["sha256"], fingerprint)
            check("source_inventory", source_id, "file size in bytes",
                  int(row["file_size_bytes"]), path.stat().st_size)
            metadata = subprocess.check_output(["pdfinfo", str(path)], text=True)
            pages = int(re.search(r"^Pages:\s+(\d+)", metadata, re.M)[1])
            check("source_inventory", source_id, "physical page count", int(row["page_count"]), pages)
        elif row["acquisition_status"] == "unavailable":
            check("statssa_sector_employment", source_id, "historical attachment acquisition",
                  "Download original attachment", "Unavailable from this environment", row["notes"],
                  "source_limitation")
    return source_ids


def check_anchors(targets, baseline, qlfs):
    for level, target_pair, baseline_pair in (
        ("top_management", ("20.0", "15.0"), ("9.9", "6.2")),
        ("senior_management", ("25.0", "15.0"), ("15.9", "8.2")),
    ):
        for gender, target, observed in zip(GENDERS[:2], target_pair, baseline_pair, strict=True):
            keys = dict(sector_id="agriculture", occupational_level=level, gender=gender)
            for name, items, field, expected in (
                ("ee_sector_targets", [r for r in targets if r["policy_version"] == "draft_2023"],
                 "target_pct", target),
                ("ee_gazette_workforce_baseline_2022", baseline, "observed_pct", observed),
            ):
                row = next(r for r in items if all(r[k] == v for k, v in keys.items()))
                check(name, "EE2023", f"Agriculture {level}, {gender} anchor", Decimal(expected), row[field])
    for sector_id, anchor in (
        ("accommodation_food", ("56.7", "78.3")), ("agriculture", ("34.0", "52.6")),
        ("manufacturing", ("49.1", "66.0")), ("mining", ("57.5", "64.5")),
    ):
        for level, expected in zip(LEVELS, anchor, strict=True):
            row = next(r for r in targets if r["policy_version"] == "final_2025"
                       and r["sector_id"] == sector_id and r["occupational_level"] == level
                       and r["gender"] == "total")
            check("ee_sector_targets", "EE2025", f"{sector_id}, {level} total anchor",
                  Decimal(expected), row["target_pct"])
    expected = (17055, 920, 449, 1610, 109, 1390, 3424, 1113, 2930, 3988, 1111)
    current = {r["industry_standardised"]: r["published_employment_value"]
               for r in qlfs if r["observation_period"] == "2025Q3"}
    for industry, anchor in zip(INDUSTRIES.values(), expected, strict=True):
        check("statssa_sector_employment", "QLFS2025Q3", f"{industry} 2025 anchor (thousands)",
              anchor, current[industry])


def check_coverage(targets, baseline, reference, qlfs, source_ids):
    sector_ids = {r["sector_id"] for r in reference}
    ee_keys = {(sector, level, gender) for sector in sector_ids for level in LEVELS for gender in GENDERS}
    for name, source, rows, field in (
        ("ee_sector_targets", "EE2023", [r for r in targets if r["policy_version"] == "draft_2023"], "target_pct"),
        ("ee_sector_targets", "EE2025", [r for r in targets if r["policy_version"] == "final_2025"], "target_pct"),
        ("ee_gazette_workforce_baseline_2022", "EE2023", baseline, "observed_pct"),
    ):
        check(name, source, "row count", 108, len(rows))
        actual = {(r["sector_id"], r["occupational_level"], r["gender"]) for r in rows}
        check(name, source, "unique complete sector × level × gender keys", True,
              actual == ee_keys and len(actual) == len(rows))
        check(name, source, "nonmissing percentages in [0, 100] with source references", len(rows),
              sum(0 <= r[field] <= 100 and r["source_id"] == source and bool(r["source_page_pdf"])
                  and bool(r["source_page_printed"]) for r in rows))
    check("ee_sector_targets", "EE2023; EE2025", "unique target IDs", 216,
          len({r["target_id"] for r in targets}))
    check("ee_sector_targets", "EE2023; EE2025", "same-version status, population and horizon", True,
          {(r["policy_version"], r["policy_status_at_publication"], r["target_population"],
            r["geographic_scope"], r["target_horizon_years"]) for r in targets} ==
          {("draft_2023", "draft", "black", "national", 5),
           ("final_2025", "final", "designated_groups", "national", 5)})
    check("ee_sector_reference", "EE2023; EE2025; EEADMIN2025; CEE24; CEE25",
          "unique canonical sector count", 18, len(sector_ids))
    expected = {(f"{year}Q3", industry) for year in range(2016, 2026) for industry in INDUSTRIES.values()}
    actual = {(r["observation_period"], r["industry_standardised"]) for r in qlfs}
    check("statssa_sector_employment", "QLFS paired Q3 PDFs", "complete unique Q3 industry keys",
          True, len(qlfs) == 110 and actual == expected)
    check("statssa_sector_employment", "QLFS paired Q3 PDFs", "quarter, scale, values and provenance",
          len(qlfs), sum(r["observation_quarter"] == 3 and r["published_unit"] == "Thousand"
                         and r["employment_persons"] == 1000 * r["published_employment_value"]
                         and r["employment_persons"] >= 0 and r["source_id"] in source_ids
                         and r["source_page_or_cell"] != "" for r in qlfs))
    for name, rows in (("ee_sector_targets", targets), ("ee_gazette_workforce_baseline_2022", baseline),
                       ("statssa_sector_employment", qlfs)):
        check(name, "source_inventory", "registered row provenance",
              len(rows), sum(r["source_id"] in source_ids for r in rows))


def main():
    source_ids = check_sources()
    draft = read_draft()
    final = read_final()
    targets, baseline = make_ee(draft, final)
    reference = make_sector_reference(draft, final)
    qlfs = read_qlfs()
    original = DATA / "raw/statssa/P02113rdQuarter2025.pdf"
    comparison = DATA / "raw/statssa/P02113rdQuarter2025_datafirst.pdf"
    check("statssa_sector_employment", "QLFS2025Q3; QLFS2025Q3_CHECK",
          "printed page 3 including all Table B cells agrees across archives", True,
          text_pages(original, 8) == text_pages(comparison, 8),
          "The files have different SHA-256 hashes and different content elsewhere in the release.")
    check_anchors(targets, baseline, qlfs)
    check_coverage(targets, baseline, reference, qlfs, source_ids)

    failures = [r for r in VALIDATION if r["status"] == "fail"]
    if failures:
        for row in failures:
            print(row)
        raise SystemExit(f"{len(failures)} supporting collection validation checks failed")

    for stem, rows in (
        ("ee_sector_targets", targets), ("ee_gazette_workforce_baseline_2022", baseline),
        ("ee_sector_reference", reference), ("statssa_sector_employment", qlfs),
        ("supporting_data_validation", VALIDATION),
    ):
        write_csv(OUT / f"{stem}.csv", rows)
        print(f"{stem}.csv  {len(rows)} rows")


if __name__ == "__main__":
    main()
