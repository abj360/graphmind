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
    test_confidence_from_payload_is_clamped
    test_min_confidence_floor_drops_weak_triples
    test_calibrate_confidence_discounts_missing_span
    test_merge_extraction_stats_accumulates
    test_require_source_span_drops_uncited_triples
    test_require_source_span_keeps_cited_triples
    test_prompt_mentions_citation_requirement_when_enabled
    test_extract_batch_covers_all_documents
    test_extract_chunks_uses_single_calls_for_small_sets
    test_describe_config_mentions_model
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


def test_confidence_from_payload_is_clamped() -> None:
    """Checks that out-of-range model confidence scores are clamped."""
    payload = json.dumps(
        [
            {
                "subject": {"name": "Alice"},
                "predicate": "founded",
                "object": {"name": "Acme"},
                "confidence": 7.3,
            }
        ]
    )
    extractor = make_extractor(payload)
    triples = extractor.extract_text("doc-1", "text")
    assert triples[0].confidence == 1.0


def test_min_confidence_floor_drops_weak_triples() -> None:
    """Checks that triples below min_confidence are dropped and counted."""
    payload = json.dumps(
        [
            {
                "subject": {"name": "A"},
                "predicate": "p",
                "object": {"name": "B"},
                "confidence": 0.2,
            },
            {
                "subject": {"name": "C"},
                "predicate": "p",
                "object": {"name": "D"},
                "confidence": 0.9,
            },
        ]
    )
    extractor = make_extractor(payload, min_confidence=0.5)
    triples = extractor.extract_text("doc-1", "text")
    assert len(triples) == 1
    assert extractor.stats.dropped_low_confidence == 1


def test_calibrate_confidence_discounts_missing_span() -> None:
    """Checks that calibration discounts scores lacking a citation."""
    assert calibrate_confidence(1.0, has_span=False) == 0.8
    assert calibrate_confidence(0.5, has_span=True) == 0.5


def test_merge_extraction_stats_accumulates() -> None:
    """Checks that stats merging sums every counter."""
    target = ExtractionStats(calls_made=1, triples_extracted=2)
    source = ExtractionStats(calls_made=3, dropped_low_confidence=4)
    merge_extraction_stats(target, source)
    assert target.calls_made == 4
    assert target.triples_extracted == 2
    assert target.dropped_low_confidence == 4


def test_require_source_span_drops_uncited_triples() -> None:
    """Checks that require_source_span drops triples without citations."""
    extractor = make_extractor(PAYLOAD, require_source_span=True)
    triples = extractor.extract_text("doc-1", "Alice founded Acme.")
    assert triples == []
    assert extractor.stats.dropped_missing_span == 1


def test_require_source_span_keeps_cited_triples() -> None:
    """Checks that cited triples survive the citation requirement."""
    payload = json.dumps(
        [
            {
                "subject": {"name": "Alice", "entity_type": "PERSON"},
                "predicate": "founded",
                "object": {"name": "Acme", "entity_type": "ORG"},
                "confidence": 0.9,
                "source_span": {"start": 0, "end": 19, "text": "Alice founded Acme."},
            }
        ]
    )
    extractor = make_extractor(payload, require_source_span=True)
    triples = extractor.extract_text("doc-1", "Alice founded Acme.")
    assert len(triples) == 1
    assert triples[0].source_span is not None


def test_prompt_mentions_citation_requirement_when_enabled() -> None:
    """Checks that citation-requiring configs render the citation block."""
    client = FakeLLMClient([PAYLOAD])
    from extract.prompts.config import PromptConfig

    extractor = TripleExtractor(client, ExtractionConfig(), PromptConfig(require_citations=True))
    extractor.extract_text("doc-1", "Alice founded Acme.")
    assert "source_span" in client.prompts[0]


def test_extract_batch_covers_all_documents() -> None:
    """Checks that batch extraction processes every supplied document."""
    first = json.dumps(
        [
            {
                "doc_id": "d1",
                "subject": {"name": "Alice"},
                "predicate": "founded",
                "object": {"name": "Acme"},
                "confidence": 0.9,
            },
            {
                "doc_id": "d2",
                "subject": {"name": "Bob"},
                "predicate": "joined",
                "object": {"name": "Acme"},
                "confidence": 0.8,
            },
        ]
    )
    second = json.dumps(
        [
            {
                "doc_id": "d3",
                "subject": {"name": "Cid"},
                "predicate": "runs",
                "object": {"name": "Ops"},
                "confidence": 0.7,
            },
        ]
    )
    client = FakeLLMClient([first, second])
    extractor = TripleExtractor(client, ExtractionConfig(batch_size=2))
    documents = [("d1", "t1"), ("d2", "t2"), ("d3", "t3")]
    triples = extractor.extract_batch(documents)
    assert len(triples) == 3
    assert extractor.stats.calls_made == 2


def test_extract_chunks_uses_single_calls_for_small_sets() -> None:
    """Checks that small chunk sets use per-chunk calls, not batching."""
    from extract.chunker import TextChunk

    client = FakeLLMClient([PAYLOAD])
    extractor = TripleExtractor(client, ExtractionConfig(batch_size=5))
    chunks = [TextChunk("d1", 0, "text one", 0, 8), TextChunk("d2", 0, "text two", 0, 8)]
    extractor.extract_chunks(chunks)
    assert len(client.prompts) == 2


def test_describe_config_mentions_model() -> None:
    """Checks that the config summary mentions the model name."""
    extractor = make_extractor()
    assert "model=" in extractor.describe_config()
