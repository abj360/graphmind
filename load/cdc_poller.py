#!/usr/bin/env python3
"""
cdc_poller.py --- change-data-capture polling for incremental corpus ingestion

Contains:
    logger
    ChangeKind: kinds of observed source changes
    ChangeEvent: one observed source document change
    PollerConfig: tuning for the CDC polling loop
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
