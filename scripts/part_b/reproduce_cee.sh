#!/bin/sh
set -eu
python3 scripts/part_b/extract_validate.py
python3 scripts/part_b/extract_cee.py
python3 scripts/part_b/catalog_cee.py
for y in 2023 2025 2022 2021 2020 2019 2017; do python3 scripts/part_b/extend_cee.py "$y"; done
for y in 2018 2016; do python3 scripts/part_b/extend_early_cee.py "$y"; done
python3 scripts/part_b/extend_eap.py
python3 scripts/part_b/extend_coverage.py
python3 scripts/part_b/sector_coverage_cee.py
python3 scripts/part_b/finalize_cee.py
python3 scripts/part_b/verification_log.py
