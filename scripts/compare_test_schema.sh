#!/usr/bin/env bash
# =============================================================================
# compare_test_schema.sh — diff the local test schema against the cloud testing
# project's schema.
#
# Runs scripts/dump_schema.py twice into temp files:
#   1. TESTING=true TEST_ENV_FILE=.env.test.local   (local disposable DB)
#   2. TESTING=true TEST_ENV_FILE=.env.test         (cloud testing project)
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

echo "[compare_test_schema] Dumping cloud testing schema (.env.test)..."
( cd "$ROOT" && TESTING=true TEST_ENV_FILE="$ROOT/.env.test" \
    "$PY" scripts/dump_schema.py "$CLOUD_DUMP" )

echo "[compare_test_schema] Unified diff (local vs cloud testing):"
diff -u "$LOCAL_DUMP" "$CLOUD_DUMP" || true
