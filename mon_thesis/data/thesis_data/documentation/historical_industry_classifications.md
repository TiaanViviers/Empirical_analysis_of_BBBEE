# Historical JSE Bulletin industry classifications

Processed 5 local workbooks, 6,255 identifiable security rows and 133 distinct raw labels. Missing requested cross-check months: 2018-09, 2025-04. No additional acquisition was performed.
Of 4,506 unmatched security/month rows, 4,404 carry explicit likely-non-company flags and 102 do not. The manual queue prioritizes eligible instruments with missing event classifications; current reference names/tickers are kept in separate reference fields, never presented as verified historical labels.

## Interpretation and dates

These are historical JSE Monthly Bulletin NATURE OF BUSINESS descriptions. No formal equivalence to ICB or ICB codes is asserted. Abbreviations, spelling and changes over time remain unchanged in the raw label. All original workbooks are unchanged and retained outside the package.
Bulletin month is the reporting month, stored as its first day for sorting, not a publication date. Sheet names and TRADING STATISTICS FOR headings agree. Actual publication dates and pre-announcement availability are unknown for every supplied source. All event dates are provisional and reused from the existing event configuration without new research. Event classifications are provisional prior-reporting-month snapshots, not certified information sets available at announcement. No publication date is invented.

## Matching and scope

All identifiable security rows are retained, including ETFs, notes, warrants, preference shares, investment products and incomplete identities. Rows without name/code (payment continuations, blanks and explanatory/header rows) are individually accounted for in historical_industry_row_audit.csv in the engineering reports. No payment amount creates a security. Label-only rows enter manual review. Repeated share codes in a month block matching. Conflicting event/instrument records are excluded rather than collapsed.
Automatic matches require a ticker candidate AND the same normalized security name, or an enumerated source-supported display variant. Normalization removes punctuation/case and expands only: {"co": "company", "corp": "corporation", "grp": "group", "hldg": "holdings", "hldgs": "holdings", "hlds": "holdings", "ltd": "limited", "prop": "property"}. It does not remove security-class markers. Exact names alone under different tickers are review suggestions. The provider _DEL suffix is considered a ticker candidate only with validated name; multiple validated IDs remain ambiguous. No fuzzy match, inferred rename or unsupported ticker change enters the event dataset.
Reference labels come from historical-price export labels and the 2026-11-23 Screener snapshot. Their agreement supports an instrument mapping, not verified historical legal identity. Renames, reorganizations and ticker reuse with incompatible names remain unresolved. Current Listed/Delisted status is never used to match, filter or establish historical status. All 1,869 price IDs and 1,872 metadata IDs are considered, including the three metadata-only IDs.
match_confidence=high_label_concordance denotes agreement under these conservative label rules, not independent identifier-history verification. Every accepted match records method and evidence. The engineering manual-review CSV includes every ambiguous/unmatched bulletin row and each eligible price instrument lacking an event classification; counts refer to security/month records unless described as distinct instruments.

## Explicit display variants

The following variants use only visible source-label spelling, abbreviation or truncation evidence. They establish no corporate-action history. Substantive name changes remain in review.

| Code | Bulletin name | Reference label | Evidence |
| --- | --- | --- | --- |
| AEE | African Equity Emp Inv Ltd | African Equity Emp Inv L | Exact visible reference prefix (24 characters); remaining bulletin suffix 'td'; local display truncation, no rename inferred |
| AFH | Alexander Forbes Grp Hldgs | Alexander Forbes Grp Hld | Exact visible reference prefix (24 characters); remaining bulletin suffix 'gs'; local display truncation, no rename inferred |
| ANH | Anheuser-Busch InBev SA NV | Anheuser-Busch Inbev Sa | Exact visible reference prefix (23 characters); remaining bulletin suffix ' NV'; local display truncation, no rename inferred |
| APN | Aspen Pharmacare Hldgs Ltd | Aspen Pharmacare Hldgs L | Exact visible reference prefix (24 characters); remaining bulletin suffix 'td'; local display truncation, no rename inferred |
| CIL | Cons Infrastructure Grp Ltd | Cons Infrastructure Grp | Exact visible reference prefix (23 characters); remaining bulletin suffix ' Ltd'; local display truncation, no rename inferred |
| EHS | Evraz Highveld Steel & Van | Evraz Highveld Steel & V | Exact visible reference prefix (24 characters); remaining bulletin suffix 'an'; local display truncation, no rename inferred |
| FTH | Frontier Transport Hldg Ld | Frontier Transport Hldg | Exact visible reference prefix (23 characters); remaining bulletin suffix ' Ld'; local display truncation, no rename inferred |
| GSH | Grindrod Shipping Hldg Ltd | Grindrod Shipping Hldg L | Exact visible reference prefix (24 characters); remaining bulletin suffix 'td'; local display truncation, no rename inferred |
| ILU | Indluplace Properties Ltd | Indluplace Properties Lt | Exact visible reference prefix (24 characters); remaining bulletin suffix 'd'; local display truncation, no rename inferred |
| LHC | Life Healthc Grp Hldgs Ltd | Life Healthc Grp Hldgs L | Exact visible reference prefix (24 characters); remaining bulletin suffix 'td'; local display truncation, no rename inferred |
| LTE | Lighthouse Properties plc | Lighthouse Properties Pl | Exact visible reference prefix (24 characters); remaining bulletin suffix 'c'; local display truncation, no rename inferred |
| MHB | Mahube Infrastructure Ltd | Mahube Infrastructure Lt | Exact visible reference prefix (24 characters); remaining bulletin suffix 'd'; local display truncation, no rename inferred |
| NPH | Northam Platinum Hldgs Ltd | Northam Platinum Hldgs L | Exact visible reference prefix (24 characters); remaining bulletin suffix 'td'; local display truncation, no rename inferred |
| NVE | NVest Financial Hldgs Ltd | Nvest Financial Hldgs Lt | Exact visible reference prefix (24 characters); remaining bulletin suffix 'd'; local display truncation, no rename inferred |
| ORL | Oakbay Res and Energy Ltd | Oakbay Res And Energy Lt | Exact visible reference prefix (24 characters); remaining bulletin suffix 'd'; local display truncation, no rename inferred |
| PFB | Premier Fishing Brands Ltd | Premier Fishing Brands L | Exact visible reference prefix (24 characters); remaining bulletin suffix 'td'; local display truncation, no rename inferred |
| PGR | Peregrine Holdings Limited | Peregrine Holdings Limit | Exact visible reference prefix (24 characters); remaining bulletin suffix 'ed'; local display truncation, no rename inferred |
| RBP | Royal Bafokeng Platinum Ltd | Royal Bafokeng Platinum | Exact visible reference prefix (23 characters); remaining bulletin suffix ' Ltd'; local display truncation, no rename inferred |
| ROC | Rockcastle Global Real Estate Co Ltd | Rockcastle Global Real E | Exact visible reference prefix (24 characters); remaining bulletin suffix 'state Co Ltd'; local display truncation, no rename inferred |
| SAR | Safari Investments RSA Ltd | Safari Investments Rsa L | Exact visible reference prefix (24 characters); remaining bulletin suffix 'td'; local display truncation, no rename inferred |
| SSK | Stefanuti Stck Hldgs Ltd | Stefanutti Stck Hldgs Lt | 2017/2018 bulletin Stefanuti vs 2023/2025 bulletin Stefanutti, same SSK and same remaining name; IRESS label also truncates final d; spelling/display variant only |
| SSK | Stefanutti Stck Hldgs Ltd | Stefanutti Stck Hldgs Lt | Exact visible reference prefix (24 characters); remaining bulletin suffix 'd'; local display truncation, no rename inferred |
| TFG | The Foschini Group Limited | The Foschini Group Limit | Exact visible reference prefix (24 characters); remaining bulletin suffix 'ed'; local display truncation, no rename inferred |
| TXT | Textainer Group Hldgs Ltd | Textainer Group Hldgs Lt | Exact visible reference prefix (24 characters); remaining bulletin suffix 'd'; local display truncation, no rename inferred |
| UAT | Union Atlantic Minerals Ltd | Union Atlantic Minerals | Exact visible reference prefix (23 characters); remaining bulletin suffix ' Ltd'; local display truncation, no rename inferred |
| VIS | Visual International Hldgs Ltd | Visual International Hld | Exact visible reference prefix (24 characters); remaining bulletin suffix 'gs Ltd'; local display truncation, no rename inferred |
| WCC | The Waterberg Coal Co Ltd | The Waterberg Coal Co Lt | Exact visible reference prefix (24 characters); remaining bulletin suffix 'd'; local display truncation, no rename inferred |
| WTL | William Tell Holdings Ltd | William Tell Holdings Lt | Exact visible reference prefix (24 characters); remaining bulletin suffix 'd'; local display truncation, no rename inferred |

## Event coverage and denominator

The packaged historical_industry_eligible_instruments.csv lists the exact provisional denominator IDs and their audited return counts; historical_industry_coverage.csv also reports matched instruments with any valid price in −10:+10. No final econometric eligibility sample exists. Provisional eligible instrument denominator reuses reports/event_instrument_coverage.csv: definition=current_positive_volume (finite positive adjacent closes with positive volume at the return date), at least 180 benchmark-paired usable returns in sessions −250:−30 inclusive, benchmark required closes complete, and all benchmark-paired returns in −10:+10 complete. These are descriptive diagnostic returns with unverified adjustment basis. Full-period coverage and 2026 listing status play no role. Instruments are not verified unique issuers; company-candidate counts only remove explicitly flagged likely non-company securities. No issuer-level or legal exposure sample is claimed.
Eligibility input SHA-256: `21d1c69bb211dd3e733d272c7da73be2ab0ab121c128a849607ba35bc4336456`.

| Event | Date (provisional) | Bulletin | Source rows | Labels | Matched | Ambiguous | Unmatched | Classified / eligible | % | Mining candidates matched |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mining_charter_2017 | 2017-06-15 | 2017-05-01 | 820 | 86 | 376 | 31 | 413 | 163 / 202 | 80.6931 | 39 |
| mining_charter_2018 | 2018-09-27 | 2018-08-01 | 794 | 84 | 386 | 24 | 384 | 170 / 201 | 84.5771 | 37 |
| ee_draft_2023 | 2023-05-12 | 2023-04-01 | 1338 | 93 | 308 | 14 | 1016 | 159 / 171 | 92.9825 | 38 |
| ee_final_2025 | 2025-04-15 | 2025-03-01 | 1580 | 90 | 298 | 8 | 1274 | 169 / 174 | 97.1264 | 36 |
| bbbee_draft_2026 | 2026-01-29 | 2025-12-01 | 1723 | 90 | 300 | 4 | 1419 | 173 / 174 | 99.4253 | 38 |

The designated May 2017, August 2018, April 2023, March 2025 and December 2025 snapshots alone feed their corresponding events. September 2018 and April 2025 are cross-check-only; both are absent. The parser may ingest them later but event selection never substitutes them. Month-end must strictly precede the event; no retrospective filling is performed. is_retrospective is false for all event rows; preannouncement_availability_verified is also false. A strict availability-verified subset is currently empty.

## Security and mining flags

likely_investment_product is true only for these exact source labels: Actively Managed Certificates, Actively Managed ETF, Corp Debt, Exchange Traded Funds, Exchange Traded Notes, Inv. Prod, Kruger Rands, Warrants. likely_non_company_security also includes Non-eq Inv Instr, Other Sec, Pref Shares and names containing explicit preference/warrant/option/nil-paid/rights markers. These are transparent screening flags, not verified security classes; in particular Non-eq Inv Instr may describe an operating company. No rows are dropped by these flags.
mining_candidate uses only exact source labels: Aluminium, Aluminum, Coal, Copper, Diamonds & Gems, Gen Mining, Gold, Nom-ferr Metals, Plat & Prec. Met. The broad candidate list includes metal producers and does not establish direct mining activity or Mining Charter legal applicability. Iron & Steel and investment products are not inferred to be mining companies. Names alone do not set this flag.

## Adjacent snapshot checks

Every observed adjacent pair is compared by historical share code, preserving old/new names and labels in historical_industry_bulletin_differences.csv. A shared ticker is only a comparison key, not proof of continuity. Added/absent rows do not establish listing/delisting. Differences across 2018–2023 may include terminology revisions, business changes or identity changes; none is automatically reconciled. The requested September 2018 and April 2025 consistency checks cannot be run without those files.

| Earlier | Later | Difference | Securities |
| --- | --- | --- | --- |
| 2017-05 | 2018-08 | absent_in_earlier | 231 |
| 2017-05 | 2018-08 | absent_in_later | 257 |
| 2017-05 | 2018-08 | name_or_label_changed | 23 |
| 2018-08 | 2023-04 | absent_in_earlier | 964 |
| 2018-08 | 2023-04 | absent_in_later | 420 |
| 2018-08 | 2023-04 | name_or_label_changed | 156 |
| 2023-04 | 2025-03 | absent_in_earlier | 674 |
| 2023-04 | 2025-03 | absent_in_later | 432 |
| 2023-04 | 2025-03 | name_or_label_changed | 54 |
| 2025-03 | 2025-12 | absent_in_earlier | 366 |
| 2025-03 | 2025-12 | absent_in_later | 223 |
| 2025-03 | 2025-12 | name_or_label_changed | 48 |

## Sources and row preservation

| Filename | Reporting month | Worksheet | Security rows | Worksheet rows | SHA-256 |
| --- | --- | --- | --- | --- | --- |
| jse-bulletin-may-2017.xlsx | 2017-05 | May 2017 | 820 | 895 | `9809cd0a5aa7b399cbee8544fd4002c47de5e02c7a1cd29755b583a0b7a7e245` |
| securities-information-apr-2023.xlsx | 2023-04 | April 2023 | 1338 | 1407 | `937dcf28559198721136879f4d3a7da86861ac997389e399b7b7e2210395a473` |
| securities-information-aug-2018.xlsx | 2018-08 | August 2018 | 794 | 961 | `12d42fee716553649a5bdc52c9353bf94e6b280dbdd8f6b24f019101b4bf39f7` |
| securities-information-dec-2025.xlsx | 2025-12 | December 2025 | 1723 | 2194 | `6c54f67da2a9f01d66dba13c35d0b34e4b7ae94e8250d7c59fa833b8eaa9cf10` |
| securities-information-mar-2025.xlsx | 2025-03 | March 2025 | 1580 | 1638 | `069849754b6347072f5a60f1de211e9a727cf18cec93385dd48a632b886ae1e3` |

Row dispositions: {"continuation_without_identity": 830, "explanatory_before_header": 5, "header": 5, "security": 6255}. Source-row provenance is 1-based Excel row number; header_row identifies the applicable section header.

## Joining and remaining gaps

Join event_industry_classifications to prices by instrument_id after selecting event_id. Its unique key is (event_id, instrument_id); joining all events on instrument_id alone multiplies price rows. The bulletin table key is (source_file, worksheet, source_row); instrument_id is nullable. Multiple securities for an issuer remain distinct. has_historical_prices_record distinguishes the metadata-only IDs. Keep nature_of_business_raw event-specific instead of writing a single sector into instruments.parquet.
The supplied months provide substantial but incomplete provisional coverage; coverage varies by event and is measured above. The manual queue separates source absence from incompatible labels. Most early eligible-sample gaps involve differing names/tickers rather than absence of an industry in the source. Additional nearby months are therefore likely to add fewer primary matches than resolving supported identity histories. More months can improve temporal checks around listings or identifier changes, but cannot establish identity continuity or historical publication availability by themselves. Prioritize resolving the existing eligible-instrument queue and obtaining the two missing cross-check files if later authorized. Additional acquisition is not necessary to use this provisional handover, and no claim of sufficient final policy-exposure coverage is made.

## Reproduction and validation

Engineering command: `.venv/bin/python -m iress_data.historical_industry --package`. It parses only local files, uses enumerated variants in metadata/historical_industry_name_variants.csv, rewrites the two derived datasets/reports, verifies all baseline raw/original dataset hashes, and augments the portable package. Original datasets remain byte-identical. The standalone package verifier checks schemas, checksums, unique keys, source linkage, event/month mapping and prevention of post-event leakage. Tests cover parser preservation, ambiguous identities, source dates, event selection, integrity and synchronization conflicts. No econometric analysis was performed.
