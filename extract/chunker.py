#!/usr/bin/env python3
"""
chunker.py --- splits source documents into overlapping, sentence-aware chunks for extraction

Contains:
    ChunkConfig: sizing knobs for the chunking pass
    TextChunk: one immutable slice of a source document
    sentence_spans(): locates sentence boundaries in raw text
    TextChunker: converts documents into extraction-ready chunks
    TextChunker.chunk(): splits one document into chunks
    TextChunker._pack_sentences(): groups sentences under the size ceiling
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


_SENTENCE_ENDINGS = (".", "!", "?", "\n\n")


def sentence_spans(text: str) -> list[tuple[int, int]]:
    """Locates approximate sentence boundaries in raw text.

    Args:
        text: Source document text to segment.

    Returns:
        spans: (start, end) offset pairs, one per detected sentence.
    """
    spans: list[tuple[int, int]] = []
    start = 0
    for index, char in enumerate(text):
        if char in ".!?" and (index + 1 == len(text) or text[index + 1] in " \n\t"):
            spans.append((start, index + 1))
            start = index + 1
    if start < len(text):
        spans.append((start, len(text)))
    return spans


class TextChunker:
    """Splits documents into overlapping, sentence-aware chunks.

    Attributes:
        config: Sizing knobs governing chunk length and overlap.
    """

    def __init__(self, config: ChunkConfig | None = None) -> None:
        """Creates a chunker with the given sizing configuration.

        Args:
            config: Sizing overrides; defaults to ChunkConfig() when omitted.
        """
        self.config = config or ChunkConfig()

    def chunk(self, doc_id: str, text: str) -> list[TextChunk]:
        """Splits one document into a list of TextChunks.

        Args:
            doc_id: Identifier stamped onto every produced chunk.
            text: Full source text of the document.

        Returns:
            chunks: Sentence-aligned chunks covering the whole document.
        """
        if not text.strip():
            return []
        sentences = sentence_spans(text)
        windows = self._pack_sentences(sentences, len(text))
        return self._with_overlap(doc_id, text, windows)

    def _pack_sentences(
        self, sentences: list[tuple[int, int]], text_length: int
    ) -> list[tuple[int, int]]:
        """Groups consecutive sentences into windows under max_chars.

        Args:
            sentences: Sentence spans to group, in document order.
            text_length: Total character length of the source document.

        Returns:
            windows: (start, end) spans, each at most max_chars wide.
        """
        windows: list[tuple[int, int]] = []
        window_start: int | None = None
        window_end = 0
        for span_start, span_end in sentences:
            if window_start is None:
                window_start, window_end = span_start, span_end
                continue
            if span_end - window_start > self.config.max_chars:
                windows.append((window_start, window_end))
                window_start, window_end = span_start, span_end
            else:
                window_end = span_end
        if window_start is not None:
            windows.append((window_start, min(window_end, text_length)))
        return windows
