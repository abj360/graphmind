#!/usr/bin/env python3
"""
test_chunker.py --- unit tests for the text chunker

Contains:
"""

import pytest

from extract.chunker import (
    ChunkConfig,
    TextChunker,
    budget_batches,
    estimate_tokens,
    sentence_spans,
    validate_config,
)
