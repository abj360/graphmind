#!/usr/bin/env python3
"""
embedding.py --- embedding providers for entity canonicalization

Contains:
    EmbeddingProvider: minimal embedding interface
    cosine_similarity(): computes cosine similarity of two vectors
    NgramEmbeddingProvider: deterministic local character-ngram embedder
    NgramEmbeddingProvider.embed(): hashes n-grams into a vector
    OpenAIEmbeddingProvider: hosted embedding provider adapter
    build_default_provider(): selects the configured provider
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

    def embed(self, text: str) -> list[float]:
        """Computes a hashed character-ngram vector for one text.

        Args:
            text: Entity name or description to embed.

        Returns:
            vector: L2-normalized embedding of hashed n-gram counts.
        """
        vector = [0.0] * self.dimensions
        normalized = " ".join(text.casefold().split())
        padded = f" {normalized} "
        for index in range(len(padded) - self.ngram_size + 1):
            ngram = padded[index : index + self.ngram_size]
            bucket = int(hashlib.blake2b(ngram.encode(), digest_size=4).hexdigest(), 16)
            vector[bucket % self.dimensions] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0.0:
            return vector
        return [value / norm for value in vector]


class OpenAIEmbeddingProvider:
    """Adapts the OpenAI embeddings API to the EmbeddingProvider protocol.

    Attributes:
        model: Hosted embedding model identifier.
        api_key_env: Environment variable holding the API key.
    """

    def __init__(
        self, model: str = "text-embedding-3-small", api_key_env: str = "OPENAI_API_KEY"
    ) -> None:
        """Creates a hosted embedding provider adapter.

        Args:
            model: Embedding model identifier to request.
            api_key_env: Environment variable name carrying the API key.
        """
        self.model = model
        self.api_key_env = api_key_env

    def embed(self, text: str) -> list[float]:
        """Computes an embedding via the hosted embeddings API.

        Args:
            text: Entity name or description to embed.

        Returns:
            vector: Hosted embedding for the text.
        """
        from openai import OpenAI  # local import: optional dependency

        client = OpenAI()
        response = client.embeddings.create(model=self.model, input=text)
        return list(response.data[0].embedding)


def build_default_provider(env: dict[str, str] | None = None) -> EmbeddingProvider:
    """Selects an embedding provider from environment configuration.

    Args:
        env: Environment mapping; offline n-gram provider is the default.

    Returns:
        provider: Configured embedding provider instance.
    """
    import os

    active = env if env is not None else dict(os.environ)
    if active.get("GRAPHMIND_EMBEDDING_PROVIDER", "ngram") == "openai":
        return OpenAIEmbeddingProvider()
    return NgramEmbeddingProvider()
