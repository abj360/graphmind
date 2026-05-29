#!/usr/bin/env python3
"""
test_entity_resolver.py --- unit tests for embedding-based entity resolution

Contains:
    test_exact_duplicates_merge
    test_similar_names_merge_with_ngram_embeddings
    test_distinct_entities_stay_separate
    test_borderline_pairs_are_flagged_for_review
    test_resolution_rewrites_object_endpoints_too
    test_cosine_similarity_identical_vectors
    test_cosine_similarity_rejects_length_mismatch
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


def test_distinct_entities_stay_separate() -> None:
    """Checks that genuinely different entities are not merged."""
    triples = [make_triple("Alice"), make_triple("Bob", "joined", "Acme")]
    result = EntityResolver().resolve(triples)
    names = {triple.subject.name for triple in result.triples}
    assert len(names) == 2


def test_borderline_pairs_are_flagged_for_review() -> None:
    """Checks that mid-similarity pairs land in the review queue."""
    resolver = EntityResolver(threshold=0.99, review_floor=0.5)
    triples = [make_triple("Acme Corp"), make_triple("Acme Corporation", "acquired", "ByteWorks")]
    result = resolver.resolve(triples)
    assert result.borderline


def test_resolution_rewrites_object_endpoints_too() -> None:
    """Checks that canonicalization rewrites both subjects and objects."""
    triples = [make_triple("Alice", "founded", "ACME"), make_triple("Bob", "joined", "Acme")]
    result = EntityResolver().resolve(triples)
    objects = {triple.object.name for triple in result.triples}
    assert len(objects) == 1


def test_cosine_similarity_identical_vectors() -> None:
    """Checks that identical vectors score 1.0."""
    vector = [1.0, 2.0, 3.0]
    assert abs(cosine_similarity(vector, vector) - 1.0) < 1e-9


def test_cosine_similarity_rejects_length_mismatch() -> None:
    """Checks that mismatched vector lengths score 0.0."""
    assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0
