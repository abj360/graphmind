#!/usr/bin/env bash
# verify_backup.sh --- integrity-checks every backup archive in the backup dir
set -euo pipefail

BACKUP_DIR="${GRAPHMIND_BACKUP_DIR:-/backups}"
failures=0
