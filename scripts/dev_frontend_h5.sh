#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/../frontend"
echo "Starting frontend H5 dev server"
npm run dev:h5
