# Processing and validation summary

Dataset version 1.0.0; configuration conservative-source-1.0.0; quality rules trailing-1.0.0. The processing date and exact source/software/code fingerprints are recorded in manifest.json. All paths in the package are relative.

| Measured quantity | Final count |
| --- | --- |
| raw_source_rows | 4,789,760 |
| canonical_rows | 4,784,640 |
| identical_duplicate_extra_rows | 5,120 |
| conflicting_keys | 0 |
| empty_placeholders | 3,802,511 |
| observed_rows | 982,129 |
| unique_instruments | 1,869 |
| calendar_sessions | 2,560 |
| valid_price_observations | 980,974 |
| positive_volume_observations | 690,264 |
| zero_close_observations | 1,155 |
| zero_volume_observations | 291,865 |
| diagnostic_price_returns | 980,380 |
| unchanged_adjacent_price_observations | 387,135 |
| potential_stale_price_observations | 290,385 |
| extreme_price_changes | 3,566 |
| market_rows | 2,559 |

## Approved transformations

1. Reuse only source-hash and intermediate-hash verified streaming XLSX imports. Retain exact mnemonic/name spellings, source numeric values and nulls.
2. Compare all meaningful values on repeated instrument/date keys. Stop on any conflict. Reduce only identical copies, selecting filename, worksheet, then source-row order. Retain all source copies in lineage.
3. Validate that volume/trade counts are finite, integral and within Int64 range before conversion. Never round fractional values or convert blanks to zero. Negative integral values, if supplied, are preserved and flagged.
4. Keep all unique instrument-date keys and financial placeholders. Derive the compact table using close IS NOT NULL OR volume IS NOT NULL OR number_of_trades IS NOT NULL.
5. Process one chronologically ordered instrument stream with bounded Arrow chunks. Use only earlier/current observations for diagnostic flags; no return bridges a missing/invalid session.
6. Build descriptive instrument coverage and preserve all original batch/file provenance. Leave unverified identity/classification/listing fields null.
7. Preserve the existing J203 implementation and source levels. Keep the missing session absent and mark the next observed row as non-adjacent.
8. Validate all files before installing the build manifest; create the portable package only from validated outputs.

## Phase 1 versus final stale-price definitions

Phase 1 described full constant-price runs and flagged 290,527 potential-stale rows. The final trailing-only rule flags 290,385 rows. A run's first row cannot be flagged merely because later prices remain constant. This intentional difference prevents future information from entering row flags; it changes no source value and removes no observation.

## Verification performed

The full private-project verifier reads every Parquet page, validates schemas and non-nullability, canonical/master uniqueness, original-copy ranks, selected source ordering, every source-row lineage link, source and output hashes, null/value preservation, exact compact-subset equality including multiplicities, master coverage and unknown metadata, independent SQL reconstructions of trailing flags, and benchmark identity/values/calendar flags. Original XLSX files are checked against their before-build hashes. The audited reference counts are enforced when the audited source inventory matches; conflicting sources stop the build.

## Reproducibility

For fixed source workbooks, processing code/configuration and locked dependencies, the five Parquet datasets and generated documentation have deterministic contents and ordering. Processing/package timestamps intentionally change and therefore manifest bytes/checksums can change. manifest.json identifies this metadata variability separately from dataset checksums. The package verifier is self-contained and does not import preprocessing code or read original source workbooks.

The retained preprocessing repository provides `uv run python -m iress_data build`, `verify`, `package`, `verify-package` and `release` (build plus validated packaging). The existing `audit` and Playwright extraction commands remain available there. Researchers only loading this handover do not need that repository, the raw exports, a browser session or IRESS credentials.

## Source provenance

Source workbook filenames, SHA-256 digests, row counts, worksheet names, headers and observed cell types appear in documentation/source_inventory.json and the manifest. Each canonical company record points to its selected source file/sheet/row/hash. observation_lineage preserves the same information for every original company row, including duplicate copies. Market records carry their original row references and workbook hash. The original licensed files remain in the private extraction project.
