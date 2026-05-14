#!/usr/bin/env python3
"""
test_schema.py --- unit tests for triple schema validation

Contains:
    test_validate_triple_accepts_wellformed_payload
    test_validate_triple_rejects_blank_predicate
    test_validate_triples_drops_invalid_items
    test_validate_triples_strict_raises_with_details
    test_source_span_requires_end_after_start
    test_dedupe_triples_keeps_highest_confidence
    test_clamp_confidence_bounds_scores
    test_confidence_stats_counts_low_confidence
"""

import pytest

from extract.schema import (
    SourceSpan,
    TripleValidationError,
    clamp_confidence,
    confidence_stats,
    dedupe_triples,
    filter_by_confidence,
    validate_triple,
    validate_triples,
    validate_triples_strict,
)
from tests.unit.factories import make_triple


def test_validate_triple_accepts_wellformed_payload() -> None:
    """Checks that a well-formed raw payload validates into a Triple."""
    raw = {
        "subject": {"name": "Alice", "entity_type": "PERSON"},
        "predicate": "founded",
        "object": {"name": "Acme", "entity_type": "ORG"},
        "confidence": 0.9,
    }
    triple = validate_triple(raw, "doc-1")
    assert triple.subject.name == "Alice"
    assert triple.source_doc_id == "doc-1"


def test_validate_triple_rejects_blank_predicate() -> None:
    """Checks that a blank predicate fails validation."""
    raw = {
        "subject": {"name": "Alice"},
        "predicate": "   ",
        "object": {"name": "Acme"},
    }
    with pytest.raises(ValueError):
        validate_triple(raw, "doc-1")


def test_validate_triples_drops_invalid_items() -> None:
    """Checks that batch validation drops bad items and keeps good ones."""
    items = [
        {"subject": {"name": "Alice"}, "predicate": "founded", "object": {"name": "Acme"}},
        {"subject": {"name": "Bob"}, "predicate": "", "object": {"name": "Acme"}},
    ]
    triples = validate_triples(items, "doc-1")
    assert len(triples) == 1


def test_validate_triples_strict_raises_with_details() -> None:
    """Checks that strict validation aggregates per-item failure details."""
    items = [
        {"subject": {"name": "Alice"}, "predicate": "founded", "object": {"name": "Acme"}},
        {"subject": {"name": ""}, "predicate": "x", "object": {"name": "y"}},
    ]
    with pytest.raises(TripleValidationError) as excinfo:
        validate_triples_strict(items, "doc-1")
    assert "item 1" in str(excinfo.value)


def test_source_span_requires_end_after_start() -> None:
    """Checks that inverted source spans are rejected."""
    with pytest.raises(ValueError):
        SourceSpan(start=10, end=5, text="passage")


def test_dedupe_triples_keeps_highest_confidence() -> None:
    """Checks that deduplication keeps the highest-confidence copy."""
    low = make_triple(confidence=0.4)
    high = make_triple(confidence=0.95)
    deduped = dedupe_triples([low, high])
    assert len(deduped) == 1
    assert deduped[0].confidence == 0.95


def test_clamp_confidence_bounds_scores() -> None:
    """Checks that clamping constrains scores to the unit interval."""
    assert clamp_confidence(1.7) == 1.0
    assert clamp_confidence(-0.2) == 0.0
    assert clamp_confidence(0.5) == 0.5


def test_confidence_stats_counts_low_confidence() -> None:
    """Checks that confidence stats tally low-confidence triples."""
    triples = [make_triple(confidence=0.9), make_triple(confidence=0.3)]
    stats = confidence_stats(triples, review_threshold=0.6)
    assert stats.count == 2
    assert stats.low_confidence_count == 1
