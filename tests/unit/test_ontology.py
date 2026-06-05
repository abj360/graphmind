#!/usr/bin/env python3
"""
test_ontology.py --- unit tests for ontology schema enforcement

Contains:
    test_matching_rule_allows_triple
    test_unmatched_predicate_is_rejected
    test_empty_ontology_allows_everything
    test_enforce_partitions_kept_and_rejected
    test_rule_matching_is_predicate_case_insensitive
    test_add_rule_derives_new_ontology
    test_infer_rules_mines_observed_patterns
    test_diff_ontologies_finds_left_only_rules
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


def test_enforce_partitions_kept_and_rejected() -> None:
    """Checks that enforcement partitions triples with reasons."""
    ontology = Ontology({OntologyRule("PERSON", "founded", "ORG")})
    kept, violations = ontology.enforce(
        [make_triple("Alice", "founded", "Acme"), make_triple("Bob", "joined", "Acme")]
    )
    assert len(kept) == 1
    assert len(violations) == 1
    assert "joined" in violations[0].reason


def test_rule_matching_is_predicate_case_insensitive() -> None:
    """Checks that rule predicates match case-insensitively."""
    ontology = Ontology({OntologyRule("PERSON", "Founded", "ORG")})
    assert ontology.allows(make_triple("Alice", "founded", "Acme"))


def test_add_rule_derives_new_ontology() -> None:
    """Checks that add_rule extends the rule set immutably."""
    base = Ontology({OntologyRule("PERSON", "founded", "ORG")})
    extended = base.add_rule(OntologyRule("PERSON", "joined", "ORG"))
    assert not base.allows(make_triple("Bob", "joined", "Acme"))
    assert extended.allows(make_triple("Bob", "joined", "Acme"))


def test_infer_rules_mines_observed_patterns() -> None:
    """Checks that rule inference mines distinct observed patterns."""
    rules = infer_rules(
        [make_triple("Alice", "founded", "Acme"), make_triple("Bob", "founded", "Globex")]
    )
    assert rules == {OntologyRule("PERSON", "founded", "ORG")}


def test_diff_ontologies_finds_left_only_rules() -> None:
    """Checks that the ontology diff isolates left-only rules."""
    left = Ontology(
        {OntologyRule("PERSON", "founded", "ORG"), OntologyRule("ORG", "acquired", "ORG")}
    )
    right = Ontology({OntologyRule("PERSON", "founded", "ORG")})
    assert diff_ontologies(left, right) == {OntologyRule("ORG", "acquired", "ORG")}
