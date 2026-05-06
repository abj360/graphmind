#!/usr/bin/env python3
"""
test_entity_resolver.py --- unit tests for embedding-based entity resolution

Contains:
    test_exact_duplicates_merge
    test_similar_names_merge_with_ngram_embeddings
"""

from resolution.embedding import NgramEmbeddingProvider, cosine_similarity
from resolution.entity_resolver import (
    EntityResolver,
    duplicate_rate,
    resolve_names,
    summarize_merges,
)
from tests.unit.factories import make_triple


def test_exact_duplicates_merge() -> None:
    """Checks that identical names differing only in case are merged."""
    triples = [make_triple("Alice"), make_triple("ALICE", "joined", "Acme")]
    result = EntityResolver().resolve(triples)
    subjects = {triple.subject.name for triple in result.triples}
    assert len(subjects) == 1


def test_similar_names_merge_with_ngram_embeddings() -> None:
    """Checks that near-identical names merge under embedding similarity."""
    triples = [make_triple("Acme Corp"), make_triple("Acme Corporation", "acquired", "ByteWorks")]
    result = EntityResolver(threshold=0.7).resolve(triples)
    assert result.merges
