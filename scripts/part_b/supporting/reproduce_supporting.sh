#!/bin/sh
set -eu
cd "$(dirname "$0")/../../.."
exec python3 scripts/part_b/supporting/reproduce_supporting.py
