#!/usr/bin/env python3
"""
test_cdc_poller.py --- integration tests for CDC polling over a filesystem corpus

Contains:
    make_poller(): builds a poller over a temp corpus
    test_new_document_emits_upsert
    test_unchanged_corpus_emits_nothing
    test_modified_document_emits_new_upsert
    test_deleted_document_emits_delete
    test_state_survives_poller_restart
    test_doc_id_uses_relative_posix_path
    test_file_checksum_changes_with_content
    test_apply_events_routes_by_kind
    test_summarize_events_counts_kinds
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


def test_state_survives_poller_restart(tmp_path) -> None:
    """Checks that a fresh poller instance sees prior state, not events."""
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "a.txt").write_text("alpha")
    state = tmp_path / "state.json"
    make_poller(corpus, state).poll_once()
    assert make_poller(corpus, state).poll_once() == []


def test_doc_id_uses_relative_posix_path(tmp_path) -> None:
    """Checks that document ids are relative POSIX paths."""
    nested = tmp_path / "sub" / "doc.txt"
    nested.parent.mkdir()
    nested.write_text("x")
    assert doc_id_for_path(nested, tmp_path) == "sub/doc.txt"


def test_file_checksum_changes_with_content(tmp_path) -> None:
    """Checks that the checksum tracks content, not metadata."""
    target = tmp_path / "a.txt"
    target.write_text("alpha")
    first = file_checksum(target)
    target.write_text("beta")
    assert file_checksum(target) != first


def test_apply_events_routes_by_kind(tmp_path) -> None:
    """Checks that apply_events routes upserts and deletes correctly."""
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    target = corpus / "a.txt"
    target.write_text("alpha")
    poller = make_poller(corpus, tmp_path / "state.json")
    poller.poll_once()
    target.unlink()
    events = poller.poll_once()
    routed: dict[str, list[str]] = {"up": [], "down": []}
    apply_events(events, routed["up"].append, routed["down"].append)
    assert routed == {"up": [], "down": ["a.txt"]}


def test_summarize_events_counts_kinds(tmp_path) -> None:
    """Checks that the summary counts upserts and deletes separately."""
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "a.txt").write_text("alpha")
    (corpus / "b.txt").write_text("beta")
    poller = make_poller(corpus, tmp_path / "state.json")
    events = poller.poll_once()
    assert summarize_events(events)[ChangeKind.UPSERT] == 2
    assert filter_upserts(events) == events
