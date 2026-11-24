# Part B: CEE data collection proof of concept

## Source and scope

The [25th Commission for Employment Equity Annual Report 2024/25](https://www.labour.gov.za/DocumentCenter/Reports/Annual%20Reports/Employment%20Equity/2025/25th%20CEE%20Annual%20Report%20Final%2016%20May%202025%20%28Website%29%20%283%29.pdf), published in 2025 by the Department of Employment and Labour, reports on the 2024 EE reporting period (PDF page 24, printed page 12). Table 7 is titled “Workforce profile at the Top Management Level by Sector, Population Group and Gender” and spans printed pages 22–23 (PDF pages 34–35). Its EAP row is an economically active population benchmark, not a sector or a workforce observation. There is no table-specific footnote on either rendered page. The source inventory records the original URL, acquisition date, size and checksum.

The PDF has 108 pages, 11,674,954 bytes, and SHA-256 `96de924bb89b77cb3b2a02537b6c2e207247b5ec09ea7d802b4f44f37358fcde`. `pdfinfo` reads the PDF and `pdftotext` successfully processes all 108 pages; this establishes practical readability, not independent proof that every graphic or byte matches an external publisher checksum. The source PDF is retained unchanged.

## Dataset and definitions

There are 18 sectors, each with 10 demographic cells and one source total: 198 sector records. The EAP benchmark adds 11 records, giving 209 long-format records. `source_value` preserves the printed percentage or `NA`; `percentage` is a numeric percentage on the 0–100 scale, with the two EAP foreign-national `NA` cells stored as missing, not zero. Public administration foreign-national values of `0.0%` remain zeros. Population group and gender decode the source headings AM, CM, IM, WM, AF, CF, IF, WF, FM and FF; TOTAL is retained as an all-groups record. Source row labels are transcribed with line wrapping normalized.

`black_representation_pct` sums African, Coloured and Indian male and female cells; `black_female_representation_pct` sums their female cells. Both use the table's whole-row denominator, including foreign nationals for sectors, and are sums of rounded published percentages, not estimates from underlying counts. They repeat on each record of a row for convenience. Foreign nationals are a separate category in this table and are not assigned a population group for these sums. EAP derived sums apply to its benchmark denominator, not the workforce. The table does not provide citizenship within its African, Coloured and Indian columns, so these sums are operational proxies for the displayed categories and cannot independently establish the statutory citizenship qualification for black people. Counts, alternative denominators, and precision beyond the displayed values are unavailable.

## Validation and limitations

The two table pages were rendered with `pdftoppm` and every row and column of the extracted values checked visually against the displayed table. The script checks the PDF hash, both table titles, expected number of tokens and row names, unique sector/code keys, value ranges, and the two expected missing cells. The source has 18 sector rows and no overall workforce total. Every printed row total is 100%; EAP's eight available cells sum to 100.0%, but its two foreign-national cells are NA, so this is not a complete ten-cell sum.

Sector component sums differ from the printed total by -0.5 to +0.6 percentage points: Accommodation +0.3; Administrative -0.4; Agriculture -0.4; Arts +0.1; Construction -0.4; Education +0.3; Electricity -0.3; Financial +0.1; Health -0.2; Information +0.6; Manufacturing +0.3; Mining -0.2; Professional +0.2; Public administration +0.1; Real estate -0.5; Transportation +0.5; Water -0.3; Wholesale -0.1. These may reflect rounding or source inconsistencies; without unrounded data their cause cannot be established. No values were corrected. White male percentages are displayed to one decimal but are whole-number percentages throughout sector rows, so discrepancies should not automatically be attributed to ordinary rounding to one decimal place.

The extraction maps sector names in source order manually because PDF labels wrap across lines and sometimes interleave with values. The mapping and all extracted cells were visually checked; the script checks names occur on the correct page but does not independently prove their row assignments. PDF layout or source changes require a fresh visual review. The checksum deliberately stops the script if the PDF changes. These checks support a proof of concept, but a generalized multi-report pipeline needs report-specific table discovery, schema mappings and independent visual validation.

## Reproduction

From the repository root, with Python 3, Poppler (`curl`, `pdfinfo`, `pdftotext`, `pdftoppm`) and dependencies in `scripts/part_b/requirements.txt` installed:

```sh
python3 scripts/part_b/acquire.py
python3 scripts/part_b/extract_validate.py
pdftoppm -f 34 -l 35 -r 150 -png data/part_b/raw/cee/cee_25th_annual_report.pdf /tmp/cee-table
```

The acquisition script requires network access and refuses to replace a different existing source; it rejects downloads with a changed checksum. Extraction overwrites the two derived outputs. The current workspace's `iress-export/.venv/bin/python` provides the Python dependencies, but a separate environment can be created using the requirements file. Visual inspection is a manual validation step, not automated by the script.
