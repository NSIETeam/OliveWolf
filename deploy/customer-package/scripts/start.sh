#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
STUDIO_DIR="$ROOT_DIR/studio"
cd "$STUDIO_DIR"

docker compose up -d

echo "OliveWolf Studio is starting."
echo "Open: http://localhost:8080/"
echo "API docs: http://localhost:8080/docs"
echo "API key:"
grep '^STUDIO_API_KEY=' .env | cut -d= -f2-
