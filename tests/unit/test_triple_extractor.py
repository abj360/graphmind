#!/usr/bin/env python3
"""
test_triple_extractor.py --- unit tests for the LLM triple extractor

Contains:
    PAYLOAD: canned LLM response used across tests
    make_extractor(): builds an extractor with a scripted client
    test_extract_text_returns_validated_triples
    test_extract_text_handles_prose_wrapped_json
    test_extract_text_returns_empty_on_garbage
    test_invalid_items_are_dropped_silently
    test_retries_transient_failures_then_succeeds
    test_raises_after_exhausting_retries
"""

import json

from extract.llm_client import FailingLLMClient, FakeLLMClient
from extract.triple_extractor import (
    ExtractionConfig,
    ExtractionError,
    ExtractionStats,
    TripleExtractor,
    calibrate_confidence,
    merge_extraction_stats,
)

PAYLOAD = json.dumps(
    [
        {
            "subject": {"name": "Alice", "entity_type": "PERSON"},
            "predicate": "founded",
            "object": {"name": "Acme", "entity_type": "ORG"},
            "confidence": 0.9,
        }
    ]
)


def make_extractor(response: str = PAYLOAD, **overrides: object) -> TripleExtractor:
    """Builds an extractor wired to a scripted fake client.

    Args:
        response: Single canned completion the client returns.
        overrides: ExtractionConfig field overrides.

    Returns:
        extractor: Configured extractor ready for tests.
    """
    client = FakeLLMClient([response])
    return TripleExtractor(client, ExtractionConfig(**overrides))


def test_extract_text_returns_validated_triples() -> None:
    """Checks that a clean LLM response yields validated triples."""
    extractor = make_extractor()
    triples = extractor.extract_text("doc-1", "Alice founded Acme.")
    assert len(triples) == 1
    assert triples[0].subject.name == "Alice"
    assert extractor.stats.calls_made == 1


def test_extract_text_handles_prose_wrapped_json() -> None:
    """Checks that JSON embedded in prose is still parsed."""
    extractor = make_extractor(f"Here you go:\n{PAYLOAD}\nHope that helps.")
    triples = extractor.extract_text("doc-1", "Alice founded Acme.")
    assert len(triples) == 1


def test_extract_text_returns_empty_on_garbage() -> None:
    """Checks that unparseable responses yield no triples, not crashes."""
    extractor = make_extractor("no json here at all")
    assert extractor.extract_text("doc-1", "text") == []


def test_invalid_items_are_dropped_silently() -> None:
    """Checks that malformed array items are dropped, keeping valid ones."""
    payload = json.dumps(
        [
            {"subject": {"name": "Alice"}, "predicate": "founded", "object": {"name": "Acme"}},
            {"subject": {"name": ""}, "predicate": "x", "object": {"name": "y"}},
        ]
    )
    extractor = make_extractor(payload)
    assert len(extractor.extract_text("doc-1", "text")) == 1


def test_retries_transient_failures_then_succeeds() -> None:
    """Checks that transient client failures are retried successfully."""
    client = FailingLLMClient(failures=2, inner=FakeLLMClient([PAYLOAD]))
    extractor = TripleExtractor(client, ExtractionConfig(max_retries=2))
    triples = extractor.extract_text("doc-1", "text")
    assert len(triples) == 1
    assert extractor.stats.retries == 2


def test_raises_after_exhausting_retries() -> None:
    """Checks that persistent client failure surfaces as ExtractionError."""
    client = FailingLLMClient(failures=5, inner=FakeLLMClient([PAYLOAD]))
    extractor = TripleExtractor(client, ExtractionConfig(max_retries=1))
    try:
        extractor.extract_text("doc-1", "text")
        raised = False
    except ExtractionError:
        raised = True
    assert raised
