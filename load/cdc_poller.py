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
    StateStore.save(): persists current state atomically
    CdcPoller: watches a corpus directory for changes
    CdcPoller.scan(): snapshots the current corpus state
    CdcPoller.poll_once(): diffs state and emits change events
    CdcPoller._event(): builds one change event
    CdcPoller.run(): blocking polling loop
    apply_events(): routes events to extraction and loading
    filter_upserts(): keeps only upsert events
    summarize_events(): counts events by kind
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

    def save(self, state: dict[str, dict[str, float | str]]) -> None:
        """Persists the current per-document state atomically.

        Args:
            state: Mapping of doc_id to checksum and modified_at records.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)


class CdcPoller:
    """Polls a corpus directory and emits change events for new edits.

    Attributes:
        corpus_dir: Directory watched for source document changes.
        config: Polling loop tuning.
        store: State persistence used to survive restarts.
    """

    def __init__(self, corpus_dir: Path, config: PollerConfig | None = None) -> None:
        """Creates a poller over a corpus directory.

        Args:
            corpus_dir: Directory watched for changes.
            config: Polling tuning; defaults applied when omitted.
        """
        self.corpus_dir = corpus_dir
        self.config = config or PollerConfig()
        self.store = StateStore(self.config.state_path)

    def scan(self) -> dict[str, dict[str, float | str]]:
        """Snapshots the current checksum state of the corpus.

        Returns:
            state: Mapping of doc_id to checksum and modified_at records.
        """
        state: dict[str, dict[str, float | str]] = {}
        for path in sorted(self.corpus_dir.glob(self.config.glob_pattern)):
            if not path.is_file():
                continue
            doc_id = doc_id_for_path(path, self.corpus_dir)
            state[doc_id] = {
                "checksum": file_checksum(path),
                "modified_at": path.stat().st_mtime,
            }
        return state

    def poll_once(self) -> list[ChangeEvent]:
        """Polls once, emitting events for new, changed, and deleted docs.

        Returns:
            events: Change events since the last persisted state.
        """
        previous = self.store.load()
        current = self.scan()
        events: list[ChangeEvent] = []
        for doc_id, record in current.items():
            old = previous.get(doc_id)
            if old is None or old["checksum"] != record["checksum"]:
                events.append(self._event(doc_id, ChangeKind.UPSERT, record))
        for doc_id in previous:
            if doc_id not in current:
                events.append(self._event(doc_id, ChangeKind.DELETE, previous[doc_id]))
        self.store.save(current)
        return events

    def _event(self, doc_id: str, kind: str, record: dict[str, float | str]) -> ChangeEvent:
        """Builds one change event from a state record.

        Args:
            doc_id: Document identifier the event concerns.
            kind: ChangeKind value, upsert or delete.
            record: State record carrying checksum and modified_at.

        Returns:
            event: Immutable change event.
        """
        return ChangeEvent(
            doc_id=doc_id,
            kind=kind,
            path=self.corpus_dir / doc_id,
            checksum=str(record["checksum"]),
            modified_at=float(record["modified_at"]),
        )

    def run(self, max_iterations: int | None = None) -> None:
        """Runs the blocking polling loop, emitting events each interval.

        Args:
            max_iterations: Optional cap on loop iterations for tests.
        """
        iteration = 0
        while max_iterations is None or iteration < max_iterations:
            events = self.poll_once()
            for event in events:
                logger.info("cdc %s %s", event.kind, event.doc_id)
            iteration += 1
            if max_iterations is not None and iteration >= max_iterations:
                break
            time.sleep(self.config.interval_seconds)


def apply_events(
    events: list[ChangeEvent], reextract: Callable[[str], None], delete: Callable[[str], None]
) -> int:
    """Routes change events to re-extraction and deletion callables.

    Args:
        events: Change events to apply.
        reextract: Callable invoked with each upserted doc_id.
        delete: Callable invoked with each deleted doc_id.

    Returns:
        applied: Number of events routed.
    """
    for event in events:
        if event.kind == ChangeKind.UPSERT:
            reextract(event.doc_id)
        else:
            delete(event.doc_id)
    return len(events)


def filter_upserts(events: list[ChangeEvent]) -> list[ChangeEvent]:
    """Keeps only upsert events from a change event batch.

    Args:
        events: Mixed change events.

    Returns:
        upserts: Events of kind upsert, in original order.
    """
    return [event for event in events if event.kind == ChangeKind.UPSERT]


def summarize_events(events: list[ChangeEvent]) -> dict[str, int]:
    """Counts change events by kind.

    Args:
        events: Change events to summarize.

    Returns:
        counts: Mapping of change kind to event count.
    """
    counts = {ChangeKind.UPSERT: 0, ChangeKind.DELETE: 0}
    for event in events:
        counts[event.kind] = counts.get(event.kind, 0) + 1
    return counts
