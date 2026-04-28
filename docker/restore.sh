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
