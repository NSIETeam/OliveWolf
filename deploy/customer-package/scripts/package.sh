#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUT_DIR="$ROOT_DIR/dist"
VERSION="${1:-$(date +%Y%m%d)}"
PKG="olivewolf-studio-${VERSION}.tar.gz"

mkdir -p "$OUT_DIR"
cd "$ROOT_DIR"

tar \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='studio/storage' \
  --exclude='studio/.env' \
  --exclude='dist' \
  -czf "$OUT_DIR/$PKG" \
  README.md PRODUCT_ARCHITECTURE.md LICENSE studio deploy

echo "$OUT_DIR/$PKG"
