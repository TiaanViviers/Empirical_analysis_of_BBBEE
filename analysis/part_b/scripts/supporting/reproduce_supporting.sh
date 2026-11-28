#!/bin/sh
set -eu
cd "$(dirname "$0")/../../../.."
exec python3 analysis/part_b/scripts/supporting/reproduce_supporting.py
