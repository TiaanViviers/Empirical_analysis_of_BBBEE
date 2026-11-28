#!/bin/sh
set -eu
cd "$(dirname "$0")/../../../.."
python3 analysis/part_b/scripts/bbbee/pilot.py
python3 analysis/part_b/scripts/bbbee/extend_ownership.py
python3 analysis/part_b/scripts/bbbee/extend_compliance.py
python3 analysis/part_b/scripts/bbbee/finalize.py
python3 analysis/part_b/scripts/bbbee/verify_coordinates.py
python3 analysis/part_b/scripts/bbbee/verification_log.py
