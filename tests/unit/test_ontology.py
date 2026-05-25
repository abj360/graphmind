#!/usr/bin/env python3
"""
test_ontology.py --- unit tests for ontology schema enforcement

Contains:
    test_matching_rule_allows_triple
    test_unmatched_predicate_is_rejected
    test_empty_ontology_allows_everything
"""

from extract.ontology import (
    Ontology,
    OntologyRule,
    diff_ontologies,
    infer_rules,
)
from tests.unit.factories import make_triple


def test_matching_rule_allows_triple() -> None:
    """Checks that a triple matching a rule is allowed."""
    ontology = Ontology({OntologyRule("PERSON", "founded", "ORG")})
    assert ontology.allows(make_triple("Alice", "founded", "Acme"))


def test_unmatched_predicate_is_rejected() -> None:
    """Checks that a triple with an unknown predicate is rejected."""
    ontology = Ontology({OntologyRule("PERSON", "founded", "ORG")})
    assert not ontology.allows(make_triple("Alice", "joined", "Acme"))


def test_empty_ontology_allows_everything() -> None:
    """Checks that an empty rule set imposes no constraints."""
    ontology = Ontology(set())
    assert ontology.allows(make_triple("X", "whatever", "Y"))
