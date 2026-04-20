#!/usr/bin/env python3
"""
cdc_poller.py --- change-data-capture polling for incremental corpus ingestion

Contains:
    logger
    ChangeKind: kinds of observed source changes
    ChangeEvent: one observed source document change
    PollerConfig: tuning for the CDC polling loop
    file_checksum(): content hash for change detection
    doc_id_for_path(): stable id derived from a path
    StateStore: persists last-seen document state
    StateStore.load(): restores persisted state
"""

import hashlib
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


class ChangeKind:
    """Enumerates the kinds of source document changes."""

    UPSERT = "upsert"
    DELETE = "delete"


@dataclass(frozen=True)
class ChangeEvent:
    """Represents one observed change in the source corpus.

    Attributes:
        doc_id: Stable document identifier derived from its path.
        kind: ChangeKind value, upsert or delete.
        path: Filesystem path of the changed document.
        checksum: Content hash used to detect modifications.
        modified_at: Modification timestamp reported by the filesystem.
    """

    doc_id: str
    kind: str
    path: Path
    checksum: str
    modified_at: float


@dataclass(frozen=True)
class PollerConfig:
    """Controls the CDC polling loop behavior.

    Attributes:
        interval_seconds: Delay between consecutive polls.
        state_path: JSON file persisting the last-seen document state.
        glob_pattern: Pattern selecting which corpus files are tracked.
    """

    interval_seconds: float = 5.0
    state_path: Path = Path("out/cdc_state.json")
    glob_pattern: str = "**/*.txt"


def file_checksum(path: Path) -> str:
    """Computes the content hash used to detect document modifications.

    Args:
        path: Document file to hash.

    Returns:
        checksum: Hex digest of the file content.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def doc_id_for_path(path: Path, root: Path) -> str:
    """Derives a stable document identifier from a filesystem path.

    Args:
        path: Document file path.
        root: Corpus root the path is made relative to.

    Returns:
        doc_id: Relative POSIX path used as the document identifier.
    """
    return path.relative_to(root).as_posix()


class StateStore:
    """Persists the last-seen checksum state between polling runs.

    Attributes:
        path: JSON file the state is read from and written to.
    """

    def __init__(self, path: Path) -> None:
        """Creates a state store bound to one JSON file.

        Args:
            path: JSON file persisting checksums between runs.
        """
        self.path = path

    def load(self) -> dict[str, dict[str, float | str]]:
        """Restores the persisted per-document state.

        Returns:
            state: Mapping of doc_id to checksum and modified_at records.
        """
        if not self.path.exists():
            return {}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            logger.warning("corrupt CDC state file %s; starting fresh", self.path)
            return {}
        return data
