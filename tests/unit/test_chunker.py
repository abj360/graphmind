#!/usr/bin/env python3
"""
test_chunker.py --- unit tests for the text chunker

Contains:
    LOREM: reusable long document text
    test_empty_text_yields_no_chunks
    test_short_text_yields_single_chunk
    test_long_text_is_split_under_ceiling
    test_chunks_cover_the_whole_document
    test_overlap_carries_trailing_context
    test_sentence_spans_finds_boundaries
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


def test_long_text_is_split_under_ceiling() -> None:
    """Checks that long text splits into chunks under the size ceiling."""
    config = ChunkConfig(max_chars=300, overlap_chars=30, min_chunk_chars=50)
    chunks = TextChunker(config).chunk("doc-1", LOREM)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.text) <= config.max_chars + config.overlap_chars


def test_chunks_cover_the_whole_document() -> None:
    """Checks that chunk end offsets reach the end of the document."""
    chunks = TextChunker().chunk("doc-1", LOREM)
    assert chunks[-1].end == len(LOREM)


def test_overlap_carries_trailing_context() -> None:
    """Checks that non-initial chunks start before their window start."""
    config = ChunkConfig(max_chars=250, overlap_chars=60, min_chunk_chars=40)
    chunks = TextChunker(config).chunk("doc-1", LOREM)
    assert len(chunks) > 1
    assert chunks[1].start < chunks[0].end


def test_sentence_spans_finds_boundaries() -> None:
    """Checks that sentence segmentation finds period boundaries."""
    spans = sentence_spans("One. Two! Three?")
    assert len(spans) == 3
