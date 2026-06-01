#!/usr/bin/env sh
set -eu
if [ "$#" -lt 1 ]; then
  echo "Usage: sh scripts/package_check.sh <zip-path>"
  exit 1
fi
cd "$(dirname "$0")/.."
python tests/run_package_check.py --zip "$1"
