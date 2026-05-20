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

main() {
    shopt -s nullglob
    local archives=("${BACKUP_DIR}"/neo4j-*.tar.gz)
    if [ ${#archives[@]} -eq 0 ]; then
        printf 'no archives found in %s\n' "$BACKUP_DIR" >&2
        exit 1
    fi
    for archive in "${archives[@]}"; do
        check_one "$archive" || failures=$((failures + 1))
    done
    [ "$failures" -eq 0 ]
}

main "$@"
