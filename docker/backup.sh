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
