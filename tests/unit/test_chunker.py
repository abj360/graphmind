#!/usr/bin/env python3
"""
test_chunker.py --- unit tests for the text chunker

Contains:
    LOREM: reusable long document text
    test_empty_text_yields_no_chunks
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

LOREM = (
    "Alice founded Acme in 2011. Acme grew quickly in Leeds. "
    "The company acquired ByteWorks in 2015. ByteWorks built data tools. "
    "Acme later expanded into consulting. It opened an office in York. "
    "Revenue doubled within two years. The team hired forty engineers."
) * 6


def test_empty_text_yields_no_chunks() -> None:
    """Checks that blank input produces zero chunks."""
    assert TextChunker().chunk("doc-1", "   ") == []
