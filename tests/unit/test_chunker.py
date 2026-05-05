#!/usr/bin/env python3
"""
test_chunker.py --- unit tests for the text chunker

Contains:
    LOREM: reusable long document text
    test_empty_text_yields_no_chunks
    test_short_text_yields_single_chunk
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


def test_short_text_yields_single_chunk() -> None:
    """Checks that text under max_chars stays in one chunk."""
    chunks = TextChunker().chunk("doc-1", "Alice founded Acme.")
    assert len(chunks) == 1
    assert chunks[0].doc_id == "doc-1"
