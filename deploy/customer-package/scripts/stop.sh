#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
STUDIO_DIR="$ROOT_DIR/studio"
cd "$STUDIO_DIR"

docker compose down
