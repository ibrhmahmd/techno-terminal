#!/usr/bin/env bash
# =============================================================================
# compare_test_schema.sh — diff the local test schema against the Supabase staging
# project's schema.
#
# Runs scripts/dump_schema.py twice into temp files:
#   1. TESTING=true TEST_ENV_FILE=.env.test.local   (local disposable DB)
#   2. TESTING=true TEST_ENV_FILE=.env.staging      (Supabase staging project)
# and prints a unified diff.
#
# Never loads .env (production): only the two test env files above.
# Note: the second dump reads the cloud project; run this deliberately.
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${PYTHON:-python}"
LOCAL_DUMP="$(mktemp)"
CLOUD_DUMP="$(mktemp)"
trap 'rm -f "$LOCAL_DUMP" "$CLOUD_DUMP"' EXIT

echo "[compare_test_schema] Dumping local schema (.env.test.local)..."
( cd "$ROOT" && TESTING=true TEST_ENV_FILE="$ROOT/.env.test.local" \
    "$PY" scripts/dump_schema.py "$LOCAL_DUMP" )

echo "[compare_test_schema] Dumping Supabase staging schema (.env.staging)..."
( cd "$ROOT" && TESTING=true TEST_ENV_FILE="$ROOT/.env.staging" \
    "$PY" scripts/dump_schema.py "$CLOUD_DUMP" )

echo "[compare_test_schema] Unified diff (local vs Supabase staging):"
diff -u "$LOCAL_DUMP" "$CLOUD_DUMP" || true
