#!/usr/bin/env python3
"""
test_cdc_poller.py --- integration tests for CDC polling over a filesystem corpus

Contains:
    make_poller(): builds a poller over a temp corpus
    test_new_document_emits_upsert
    test_unchanged_corpus_emits_nothing
    test_modified_document_emits_new_upsert
    test_deleted_document_emits_delete
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


def test_new_document_emits_upsert(tmp_path) -> None:
    """Checks that a newly added document emits an upsert event."""
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "a.txt").write_text("alpha")
    poller = make_poller(corpus, tmp_path / "state.json")
    events = poller.poll_once()
    assert len(events) == 1
    assert events[0].kind == ChangeKind.UPSERT
    assert events[0].doc_id == "a.txt"


def test_unchanged_corpus_emits_nothing(tmp_path) -> None:
    """Checks that an unchanged corpus emits no events on re-poll."""
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "a.txt").write_text("alpha")
    poller = make_poller(corpus, tmp_path / "state.json")
    poller.poll_once()
    assert poller.poll_once() == []


def test_modified_document_emits_new_upsert(tmp_path) -> None:
    """Checks that a content change re-emits an upsert for the document."""
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    target = corpus / "a.txt"
    target.write_text("alpha")
    poller = make_poller(corpus, tmp_path / "state.json")
    poller.poll_once()
    target.write_text("alpha beta")
    events = poller.poll_once()
    assert len(events) == 1
    assert events[0].kind == ChangeKind.UPSERT


def test_deleted_document_emits_delete(tmp_path) -> None:
    """Checks that a removed document emits a delete event."""
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    target = corpus / "a.txt"
    target.write_text("alpha")
    poller = make_poller(corpus, tmp_path / "state.json")
    poller.poll_once()
    target.unlink()
    events = poller.poll_once()
    assert len(events) == 1
    assert events[0].kind == ChangeKind.DELETE
