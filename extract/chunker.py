#!/usr/bin/env python3
"""
chunker.py --- splits source documents into overlapping, sentence-aware chunks for extraction

Contains:
    ChunkConfig: sizing knobs for the chunking pass
    TextChunk: one immutable slice of a source document
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkConfig:
    """Controls how source text is split into extraction chunks.

    Attributes:
        max_chars: Hard ceiling on chunk length in characters.
        overlap_chars: Trailing characters repeated into the next chunk.
        min_chunk_chars: Chunks shorter than this merge into the previous one.
    """

    max_chars: int = 1_200
    overlap_chars: int = 120
    min_chunk_chars: int = 200


@dataclass(frozen=True)
class TextChunk:
    """Represents one slice of a source document ready for extraction.

    Attributes:
        doc_id: Identifier of the document the chunk came from.
        index: Zero-based position of the chunk within the document.
        text: Chunk content, sentence-aligned where possible.
        start: Inclusive character offset within the source document.
        end: Exclusive character offset within the source document.
    """

    doc_id: str
    index: int
    text: str
    start: int
    end: int
