#!/usr/bin/env bash
# backup.sh --- dumps the Neo4j database to a timestamped archive
set -euo pipefail

NEO4J_HOST="${NEO4J_HOST:-neo4j}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-graphmind-dev}"
BACKUP_DIR="${GRAPHMIND_BACKUP_DIR:-/backups}"
RETENTION_DAYS="${GRAPHMIND_BACKUP_RETENTION_DAYS:-14}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE="${BACKUP_DIR}/neo4j-${TIMESTAMP}.tar.gz"

log() {
    printf '[backup %s] %s\n' "$(date +%H:%M:%S)" "$1"
}

fail() {
    log "ERROR: $1" >&2
    exit 1
}

require_tools() {
    for tool in cypher-shell tar; do
        command -v "$tool" >/dev/null 2>&1 || fail "missing required tool: $tool"
    done
}

wait_for_neo4j() {
    log "waiting for neo4j at ${NEO4J_HOST}:7687"
    for attempt in $(seq 1 30); do
        if cypher-shell -a "bolt://${NEO4J_HOST}:7687" -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
            "RETURN 1" >/dev/null 2>&1; then
            log "neo4j is reachable"
            return 0
        fi
        sleep 2
    done
    fail "neo4j did not become reachable in time"
}

dump_database() {
    local staging="$1"
    log "exporting nodes"
    cypher-shell -a "bolt://${NEO4J_HOST}:7687" -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
        "MATCH (n) RETURN n" --format plain > "${staging}/nodes.txt"
    log "exporting relationships"
    cypher-shell -a "bolt://${NEO4J_HOST}:7687" -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
        "MATCH ()-[r]->() RETURN r" --format plain > "${staging}/relationships.txt"
}

pack_archive() {
    local staging="$1"
    mkdir -p "$BACKUP_DIR"
    tar -czf "$ARCHIVE" -C "$staging" .
    log "wrote ${ARCHIVE}"
}

prune_old_backups() {
    log "pruning backups older than ${RETENTION_DAYS} days"
    find "$BACKUP_DIR" -name 'neo4j-*.tar.gz' -mtime "+${RETENTION_DAYS}" -delete
}

verify_archive() {
    tar -tzf "$ARCHIVE" >/dev/null 2>&1 || fail "archive ${ARCHIVE} is corrupt"
    log "archive verified"
}
