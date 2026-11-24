#!/bin/sh
set -eu
cd "$(dirname "$0")/../../.."
python3 scripts/part_b/bbbee/pilot.py
python3 scripts/part_b/bbbee/extend_ownership.py
python3 scripts/part_b/bbbee/extend_compliance.py
