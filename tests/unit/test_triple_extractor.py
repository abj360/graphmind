#!/usr/bin/env python3
"""
test_triple_extractor.py --- unit tests for the LLM triple extractor

Contains:
    PAYLOAD: canned LLM response used across tests
    make_extractor(): builds an extractor with a scripted client
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
