#!/usr/bin/env python3
"""
test_ontology.py --- unit tests for ontology schema enforcement

Contains:
    test_matching_rule_allows_triple
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
