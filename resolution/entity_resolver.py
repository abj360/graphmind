#!/usr/bin/env python3
"""
entity_resolver.py --- embedding-based canonicalization of duplicate entities

Contains:
    MergeDecision: one canonicalization applied to an entity
    ResolutionResult: resolved triples plus merge bookkeeping
    EntityResolver: canonicalizes entities via embedding similarity
"""

from dataclasses import dataclass

from extract.schema import Triple
from resolution.embedding import EmbeddingProvider, NgramEmbeddingProvider, cosine_similarity


@dataclass(frozen=True)
class MergeDecision:
    """Records one entity merged into a canonical representative.

    Attributes:
        canonical: Representative name chosen for the cluster.
        alias: Duplicate name folded into the representative.
        similarity: Cosine similarity that justified the merge.
    """

    canonical: str
    alias: str
    similarity: float


@dataclass(frozen=True)
class ResolutionResult:
    """Bundles resolved triples with the decisions that produced them.

    Attributes:
        triples: Triples rewritten to canonical entity names.
        merges: Merge decisions applied during resolution.
        borderline: Merge candidates below auto-merge but above review floor.
    """

    triples: list[Triple]
    merges: list[MergeDecision]
    borderline: list[MergeDecision]


class EntityResolver:
    """Canonicalizes duplicate entities using embedding cosine similarity.

    Attributes:
        provider: Embedding provider used to vectorize entity names.
        threshold: Similarity at or above which entities auto-merge.
        review_floor: Similarity above which borderline pairs are flagged
            for human review instead of being ignored.
    """

    def __init__(
        self,
        provider: EmbeddingProvider | None = None,
        threshold: float = 0.85,
        review_floor: float = 0.7,
    ) -> None:
        """Creates a resolver with an injected embedding provider.

        Args:
            provider: Embedding backend; offline n-gram provider by default.
            threshold: Cosine similarity floor for automatic merges.
            review_floor: Cosine similarity floor for review candidates.
        """
        self.provider = provider or NgramEmbeddingProvider()
        self.threshold = threshold
        self.review_floor = review_floor
