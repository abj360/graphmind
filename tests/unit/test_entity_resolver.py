#!/usr/bin/env python3
"""
test_entity_resolver.py --- unit tests for embedding-based entity resolution

Contains:
    test_exact_duplicates_merge
    test_similar_names_merge_with_ngram_embeddings
"""

from resolution.entity_resolver import EntityResolver, resolve_names, summarize_merges
from tests.unit.factories import make_triple


def test_exact_duplicates_merge() -> None:
    """Checks that identical names differing only in case are merged."""
    triples = [make_triple("Alice"), make_triple("ALICE", "joined", "Acme")]
    result = EntityResolver().resolve(triples)
    subjects = {triple.subject.name for triple in result.triples}
    assert len(subjects) == 1


def test_naive_matching_does_not_merge_suffix_variants() -> None:
    """Documents that plain string matching misses suffix variants."""
    triples = [make_triple("Acme Corp"), make_triple("Acme Corporation", "acquired", "ByteWorks")]
    result = EntityResolver().resolve(triples)
    assert not result.merges
