#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
STUDIO_DIR="$ROOT_DIR/studio"

cd "$STUDIO_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install Docker Engine and retry."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 is required."
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  API_KEY="olivewolf-$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(24))
PY
)"
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/^STUDIO_API_KEY=.*/STUDIO_API_KEY=${API_KEY}/" .env
  else
    sed -i "s/^STUDIO_API_KEY=.*/STUDIO_API_KEY=${API_KEY}/" .env
  fi
  echo "Created .env with STUDIO_API_KEY=${API_KEY}"
fi

mkdir -p storage

echo "Building OliveWolf Studio..."
docker compose build

echo "Install completed. Run: deploy/customer-package/scripts/start.sh"
