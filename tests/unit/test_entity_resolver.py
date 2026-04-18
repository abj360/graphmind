#!/usr/bin/env python3
"""
test_entity_resolver.py --- unit tests for embedding-based entity resolution

Contains:
    test_exact_duplicates_merge
"""

from resolution.entity_resolver import EntityResolver, resolve_names, summarize_merges
from tests.unit.factories import make_triple


def test_exact_duplicates_merge() -> None:
    """Checks that identical names differing only in case are merged."""
    triples = [make_triple("Alice"), make_triple("ALICE", "joined", "Acme")]
    result = EntityResolver().resolve(triples)
    subjects = {triple.subject.name for triple in result.triples}
    assert len(subjects) == 1
