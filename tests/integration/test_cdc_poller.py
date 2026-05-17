#!/usr/bin/env python3
"""
test_cdc_poller.py --- integration tests for CDC polling over a filesystem corpus

Contains:
    make_poller(): builds a poller over a temp corpus
"""

from pathlib import Path

from load.cdc_poller import (
    CdcPoller,
    ChangeKind,
    PollerConfig,
    apply_events,
    doc_id_for_path,
    file_checksum,
    filter_upserts,
    summarize_events,
)


def make_poller(corpus: Path, state: Path) -> CdcPoller:
    """Builds a poller over a temporary corpus directory.

    Args:
        corpus: Directory acting as the watched corpus.
        state: State file location for the poller.

    Returns:
        poller: Configured CDC poller.
    """
    return CdcPoller(corpus, PollerConfig(state_path=state))
