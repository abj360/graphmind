#!/usr/bin/env python3
"""
test_triple_extractor.py --- unit tests for the LLM triple extractor

Contains:
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
