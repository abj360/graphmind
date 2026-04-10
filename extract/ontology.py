#!/usr/bin/env python3
"""
ontology.py --- ontology rules and schema enforcement for extracted triples

Contains:
    OntologyRule: one allowed subject-predicate-object type pattern
    OntologyViolation: one rejected triple with its reason
    Ontology: set of rules used to enforce schema conformance
    Ontology.allows(): checks a triple against every rule
"""

import json
from dataclasses import dataclass
from pathlib import Path

from extract.schema import Triple


@dataclass(frozen=True)
class OntologyRule:
    """Defines one allowed (subject_type, predicate, object_type) pattern.

    Attributes:
        subject_type: Allowed entity type for the subject position.
        predicate: Allowed predicate phrase, case-insensitive.
        object_type: Allowed entity type for the object position.
    """

    subject_type: str
    predicate: str
    object_type: str

    def matches(self, triple: Triple) -> bool:
        """Checks whether a triple satisfies this rule's type pattern.

        Args:
            triple: Triple to test against the rule.

        Returns:
            matches: True when types and predicate all align.
        """
        return (
            triple.subject.entity_type == self.subject_type
            and triple.predicate.casefold() == self.predicate.casefold()
            and triple.object.entity_type == self.object_type
        )


@dataclass(frozen=True)
class OntologyViolation:
    """Records a triple rejected by ontology enforcement.

    Attributes:
        triple: The rejected triple.
        reason: Human-readable explanation of the rejection.
    """

    triple: Triple
    reason: str


class Ontology:
    """Enforces type-level conformance of triples against known rules.

    Attributes:
        rules: Frozen set of allowed type patterns.
        strict: When true, unmatched triples are rejected; else flagged.
    """

    def __init__(self, rules: set[OntologyRule], strict: bool = True) -> None:
        """Creates an ontology from a rule set.

        Args:
            rules: Allowed type patterns; empty set allows everything.
            strict: Whether unmatched triples are rejected outright.
        """
        self.rules = frozenset(rules)
        self.strict = strict

    def allows(self, triple: Triple) -> bool:
        """Checks whether any rule permits the given triple.

        Args:
            triple: Triple to test.

        Returns:
            allowed: True when at least one rule matches, or no rules exist.
        """
        if not self.rules:
            return True
        return any(rule.matches(triple) for rule in self.rules)
