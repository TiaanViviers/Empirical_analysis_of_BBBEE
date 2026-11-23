# IRESS Screener instrument metadata — 2026-11-23

This file describes `data/instrument_metadata_2026-11-23.parquet`, a dated capture of the user-visible IRESS Expert Screener table. Capture time: `2026-11-23T11:02:07+02:00`. The extraction used Type=Equities and Companies, Exchange=Jse Securities Exchange, Listing Status=Listed and Delisted, 100 results per page. Nineteen pages were validated against their visible ranges and instrument IDs before collection. The source CSV is retained in the data engineering repository; it is intentionally outside this portable handover. Source CSV SHA-256: `b1e0a558c43228ebe7d305cd6b232262334a6573ddaa0ae54ea42a4846ee71eb`.

## Scope and reconciliation

The snapshot has 1,872 rows and 1,872 unique `instrument_id` values. It covers every ID in the 1,869-row historical-price `instruments.parquet` master. The three snapshot-only IDs are `IMRP17:XJSE:EQU`, `IMRP18:XJSE:EQU`, and `PBT_DEL:XJSE:EQU`; `has_historical_prices_record` is false for those rows. Use an exact `instrument_id` join, not company names or ticker alone. From the master, the join is one-to-one with no missing metadata; from metadata, the three extra rows are unmatched.

## ISIN handling

`isin_raw` reproduces the provider field exactly. `isin_valid` requires strict ISO 6166 structure and a passing Luhn check digit. 1,492 values pass both; 380 are nonstandard or placeholders and remain unchanged. A passing check digit checks syntax and internal consistency, not whether the ISIN belongs to that security at any date. `isin_format_valid_source` preserves the extractor's format-only flag.

## Time and interpretation

`snapshot_date` is the local capture date and `captured_at` records the actual timezone-aware extraction time. `listing_status_snapshot`, `company_name`, `instrument_type`, `exchange`, `country`, and `isin_raw` describe the Screener display on that date. They do not establish values at earlier event dates. Do not use the snapshot's Listed/Delisted label to build historical samples, infer listing dates, or assign ordinary/preference share classes. No sector, issuer mapping, or historical status was inferred.

## Join example

```python
import pyarrow.parquet as pq
master = pq.read_table('data/instruments.parquet').select(['instrument_id', 'ticker', 'company_name'])
snapshot = pq.read_table('data/instrument_metadata_2026-11-23.parquet')
# Exact-key one-to-one join. Select master columns needed for analysis;
# Arrow joins do not support the master's list-valued company_names field.
enriched = master.join(snapshot, keys='instrument_id', join_type='left outer', right_suffix='_snapshot')
```

The package verifier checks the Parquet schema, checksums, counts, ISIN flags, and master reconciliation.
