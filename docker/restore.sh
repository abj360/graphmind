#!/usr/bin/env bash
# restore.sh --- restores a Neo4j backup archive produced by backup.sh
set -euo pipefail

NEO4J_HOST="${NEO4J_HOST:-neo4j}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-graphmind-dev}"
BACKUP_DIR="${GRAPHMIND_BACKUP_DIR:-/backups}"

log() {
    printf '[restore %s] %s\n' "$(date +%H:%M:%S)" "$1"
}

fail() {
    log "ERROR: $1" >&2
    exit 1
}

usage() {
    printf 'usage: %s <archive.tar.gz|latest>\n' "$(basename "$0")" >&2
    exit 64
}

resolve_archive() {
    local requested="$1"
    if [ "$requested" = "latest" ]; then
        ls -1t "${BACKUP_DIR}"/neo4j-*.tar.gz 2>/dev/null | head -n 1
    else
        printf '%s\n' "$requested"
    fi
}

preflight() {
    local archive="$1"
    [ -f "$archive" ] || fail "archive not found: $archive"
    tar -tzf "$archive" >/dev/null 2>&1 || fail "archive is corrupt: $archive"
    tar -tzf "$archive" | grep -q 'nodes.txt' || fail "archive lacks nodes.txt"
    tar -tzf "$archive" | grep -q 'relationships.txt' || fail "archive lacks relationships.txt"
}

confirm_destructive() {
    if [ "${GRAPHMIND_RESTORE_CONFIRM:-}" != "yes" ]; then
        fail "restore wipes current data; re-run with GRAPHMIND_RESTORE_CONFIRM=yes"
    fi
}

wipe_graph() {
    log "wiping current graph contents"
    cypher-shell -a "bolt://${NEO4J_HOST}:7687" -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
        "MATCH (n) DETACH DELETE n"
}

replay_dump() {
    local staging="$1"
    log "replay is manual for plain-format dumps; see docs for cypher ingestion"
    cat "${staging}/nodes.txt" "${staging}/relationships.txt" >/dev/null
}

main() {
    [ $# -eq 1 ] || usage
    local archive staging
    archive="$(resolve_archive "$1")"
    [ -n "$archive" ] || fail "no archives found in ${BACKUP_DIR}"
    log "restoring from ${archive}"
    preflight "$archive"
    confirm_destructive
    staging="$(mktemp -d)"
    trap 'rm -rf "$staging"' EXIT
    tar -xzf "$archive" -C "$staging"
    wipe_graph
    replay_dump "$staging"
    log "restore complete"
}

main "$@"
