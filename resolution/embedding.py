#!/usr/bin/env python3
"""
embedding.py --- embedding providers for entity canonicalization

Contains:
    EmbeddingProvider: minimal embedding interface
    cosine_similarity(): computes cosine similarity of two vectors
    NgramEmbeddingProvider: deterministic local character-ngram embedder
"""

import hashlib
import math
from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Describes the embedding interface the resolver depends on."""

    def embed(self, text: str) -> list[float]:
        """Computes a dense vector for one text.

        Args:
            text: Entity name or description to embed.

        Returns:
            vector: Dense embedding suitable for cosine similarity.
        """
        ...


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Computes the cosine similarity between two equal-length vectors.

    Args:
        left: First embedding vector.
        right: Second embedding vector.

    Returns:
        similarity: Cosine similarity between -1.0 and 1.0.
    """
    if len(left) != len(right) or not left:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if norm_left == 0.0 or norm_right == 0.0:
        return 0.0
    return dot / (norm_left * norm_right)


class NgramEmbeddingProvider:
    """Embeds text into hashed character-ngram vectors, fully offline.

    Attributes:
        dimensions: Size of the output embedding vector.
        ngram_size: Character n-gram length fed into the hasher.
    """

    def __init__(self, dimensions: int = 256, ngram_size: int = 3) -> None:
        """Creates a hashed character-ngram embedding provider.

        Args:
            dimensions: Output vector size; buckets are hashed modulo this.
            ngram_size: Character n-gram length used for features.
        """
        self.dimensions = dimensions
        self.ngram_size = ngram_size
