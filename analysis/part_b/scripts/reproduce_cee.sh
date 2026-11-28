#!/bin/sh
set -eu
python3 analysis/part_b/scripts/extract_validate.py
python3 analysis/part_b/scripts/extract_cee.py
python3 analysis/part_b/scripts/catalog_cee.py
for y in 2023 2025 2022 2021 2020 2019 2017; do python3 analysis/part_b/scripts/extend_cee.py "$y"; done
for y in 2018 2016; do python3 analysis/part_b/scripts/extend_early_cee.py "$y"; done
python3 analysis/part_b/scripts/extend_eap.py
python3 analysis/part_b/scripts/extend_coverage.py
python3 analysis/part_b/scripts/sector_coverage_cee.py
python3 analysis/part_b/scripts/finalize_cee.py
python3 analysis/part_b/scripts/verification_log.py
