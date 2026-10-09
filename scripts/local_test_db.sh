#!/usr/bin/env bash
# =============================================================================
# local_test_db.sh — disposable local Postgres for the pytest gate.
#
# A throwaway Postgres 17 container on 127.0.0.1:55432 with db/schema.sql
# applied, so tests never need the cloud Supabase database.
#
# Usage:
#   scripts/local_test_db.sh up      # start/create + init (idempotent)
#   scripts/local_test_db.sh reset   # drop + recreate techno_test, reapply schema
#   scripts/local_test_db.sh down    # remove the container
#
# Writes .env.test.local (a copy of .env.test with only DATABASE_URL swapped)
# for config.py to pick up. Supabase keys are never printed.
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER="techno-test-db"
IMAGE="postgres:17"
PORT="55432"
DB_NAME="techno_test"
DB_USER="postgres"
ENV_FILE="$ROOT/.env.test"
LOCAL_ENV="$ROOT/.env.test.local"

log()  { printf '[local_test_db] %s\n' "$*"; }
fail() { printf '[local_test_db] ERROR: %s\n' "$*" >&2; exit 1; }

container_exists() {
    docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"
}

container_running() {
    docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"
}

password_from_local_env() {
    [ -f "$LOCAL_ENV" ] || return 1
    local url
    url="$(grep -E '^DATABASE_URL=' "$LOCAL_ENV" | head -1 | cut -d= -f2-)"
    [ -n "$url" ] || return 1
    printf '%s' "$url" | sed -nE 's#^postgresql://[^:]*:([^@]*)@.*#\1#p'
}

password_from_container() {
    docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$CONTAINER" 2>/dev/null \
        | grep -E '^POSTGRES_PASSWORD=' | head -1 | cut -d= -f2- || return 1
}

resolve_password() {
    local pw
    pw="$(password_from_local_env || true)"
    if [ -n "$pw" ]; then printf '%s' "$pw"; return 0; fi
    pw="$(password_from_container || true)"
    if [ -n "$pw" ]; then printf '%s' "$pw"; return 0; fi
    return 1
}

generate_password() {
    openssl rand -hex 24
}

local_url() {
    printf 'postgresql://%s:%s@127.0.0.1:%s/%s' "$DB_USER" "$1" "$PORT" "$DB_NAME"
}

wait_ready() {
    local i
    for i in $(seq 1 60); do
        if docker exec "$CONTAINER" pg_isready -U "$DB_USER" -q >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    fail "Postgres container did not become ready in time."
}

ensure_container() {
    if container_exists; then
        if ! container_running; then
            log "Starting existing container '$CONTAINER'..."
            docker start "$CONTAINER" >/dev/null
        else
            log "Container '$CONTAINER' already running."
        fi
        wait_ready
        return 0
    fi

    local pw
    pw="$(generate_password)"
    log "Creating container '$CONTAINER' ($IMAGE) on 127.0.0.1:$PORT..."
    docker run -d \
        --name "$CONTAINER" \
        -e POSTGRES_PASSWORD="$pw" \
        -p "127.0.0.1:$PORT:5432" \
        "$IMAGE" >/dev/null
    wait_ready
}

database_exists() {
    docker exec "$CONTAINER" psql -U "$DB_USER" -tAc \
        "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';" 2>/dev/null | grep -q 1
}

schema_applied() {
    docker exec "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
        "SELECT (to_regclass('public.users') IS NOT NULL
             AND to_regclass('public.notification_templates') IS NOT NULL
             AND EXISTS (SELECT 1 FROM public.notification_templates WHERE name = 'daily_report'));" \
        2>/dev/null | grep -q '^t$'
}

apply_schema() {
    local url="$1"
    log "Applying db/schema.sql to $DB_NAME..."
    ( cd "$ROOT/db" && psql "$url" -v ON_ERROR_STOP=1 -f schema.sql >/dev/null )
}

verify_schema() {
    local url="$1"
    log "Verifying schema via scripts/verify_test_db.py..."
    ( cd "$ROOT" && python scripts/verify_test_db.py "$url" >/dev/null )
}

write_local_env() {
    local pw="$1" url
    url="$(local_url "$pw")"
    [ -f "$ENV_FILE" ] || fail "Cannot create $LOCAL_ENV: $ENV_FILE is missing."
    log "Writing $LOCAL_ENV (DATABASE_URL -> 127.0.0.1:$PORT)."
    local tmp
    tmp="$(mktemp)"
    awk -v url="$url" '/^DATABASE_URL=/{print "DATABASE_URL=" url; next} {print}' \
        "$ENV_FILE" > "$tmp"
    mv "$tmp" "$LOCAL_ENV"
}

cmd_up() {
    ensure_container
    local pw url
    pw="$(resolve_password || true)"
    if [ -z "$pw" ]; then
        # Container was just created: read the generated password back from it.
        pw="$(password_from_container)"
    fi
    [ -n "$pw" ] || fail "Could not determine the container password."
    url="$(local_url "$pw")"

    if ! database_exists; then
        log "Creating database '$DB_NAME'..."
        docker exec "$CONTAINER" psql -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;" >/dev/null
    fi

    if schema_applied; then
        log "Schema already applied; skipping schema/verify (idempotent no-op)."
    else
        apply_schema "$url"
        verify_schema "$url"
    fi

    write_local_env "$pw"
    log "Ready. Local test DB is up at 127.0.0.1:$PORT/$DB_NAME."
}

cmd_reset() {
    container_exists || fail "Container '$CONTAINER' does not exist. Run 'up' first."
    container_running || docker start "$CONTAINER" >/dev/null
    wait_ready

    local pw
    pw="$(resolve_password || true)"
    [ -n "$pw" ] || fail "Could not determine the container password."
    local url
    url="$(local_url "$pw")"

    log "Dropping and recreating database '$DB_NAME'..."
    docker exec "$CONTAINER" psql -U "$DB_USER" -c \
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$DB_NAME' AND pid <> pg_backend_pid();" >/dev/null
    docker exec "$CONTAINER" psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;" >/dev/null
    docker exec "$CONTAINER" psql -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;" >/dev/null

    apply_schema "$url"
    verify_schema "$url"
    write_local_env "$pw"
    log "Reset complete."
}

cmd_down() {
    if container_exists; then
        log "Removing container '$CONTAINER'..."
        docker rm -f "$CONTAINER" >/dev/null
    else
        log "Container '$CONTAINER' does not exist; nothing to remove."
    fi
    if [ -f "$LOCAL_ENV" ]; then
        rm -f "$LOCAL_ENV"
        log "Removed stale $LOCAL_ENV."
    fi
}

case "${1:-}" in
    up)    cmd_up ;;
    reset) cmd_reset ;;
    down)  cmd_down ;;
    *)
        printf 'Usage: %s {up|reset|down}\n' "$(basename "$0")" >&2
        exit 2
        ;;
esac
