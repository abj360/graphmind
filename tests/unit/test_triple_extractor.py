#!/usr/bin/env python3
"""
test_triple_extractor.py --- unit tests for the LLM triple extractor

Contains:
    PAYLOAD: canned LLM response used across tests
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
