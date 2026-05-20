#!/usr/bin/env bash
# verify_backup.sh --- integrity-checks every backup archive in the backup dir
set -euo pipefail

BACKUP_DIR="${GRAPHMIND_BACKUP_DIR:-/backups}"
failures=0

check_one() {
    local archive="$1"
    if tar -tzf "$archive" >/dev/null 2>&1; then
        printf 'OK      %s\n' "$archive"
    else
        printf 'CORRUPT %s\n' "$archive" >&2
        return 1
    fi
}
