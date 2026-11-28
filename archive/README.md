# Research archive

The [archive manifest](archive_manifest.csv) records original and current
locations, archive classes, sizes, SHA-256 digests and Git treatment.

- [Pre-remediation baseline](part_a/pre_remediation_2026-11-24/) preserves the
  original implementation, comparison tables, figures, diagnostics and original
  manifest. The corrected analysis still reads its comparison tables. Its local
  `derived/` Parquet directory is ignored. Use the
  [baseline reproducer](../analysis/part_a/review/remediation/README.md#original-baseline)
  to restore missing files against the original hashes.
- [Earlier independent Part A review](part_a/independent_methodology/review_report.md) and
  [remediation logs](part_a/remediation_logs/) document superseded methods and
  validation runs. Historical scripts refer to the layout of their original
  development checkout.
- `local/` contains a verified second copy of the submitted PDF and HTML,
  historical IRESS screener runs, the pre-metadata IRESS package, local browser
  profiles, extraction failure evidence and maintenance logs. These files are
  available in this workspace and excluded from Git. Browser-state integrity
  inventories are beside their archived directories. They use paths relative
  to each profile, so run `sha256sum -c` from that profile directory.
- The starting user edits and full on-disk inventory are preserved under
  `local/maintenance/`. The screener error screenshot, error text and duplicate
  run pages already deleted at intake remain recoverable from the original
  Git commit if needed.

For current methodology reviews, start with the
[research handover](../README.md#methods-and-provenance).
