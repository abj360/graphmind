#!/usr/bin/env python3
"""
ontology.py --- ontology rules and schema enforcement for extracted triples

Contains:
    OntologyRule: one allowed subject-predicate-object type pattern
    OntologyViolation: one rejected triple with its reason
    Ontology: set of rules used to enforce schema conformance
    Ontology.allows(): checks a triple against every rule
    Ontology.enforce(): partitions triples into kept and rejected
    Ontology.add_rule(): derives an ontology with one more rule
    Ontology.merge(): combines two ontologies
    Ontology.from_dict(): builds an ontology from raw mappings
    Ontology.to_dict(): serializes the rule set
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

    def enforce(self, triples: list[Triple]) -> tuple[list[Triple], list[OntologyViolation]]:
        """Partitions triples into conforming and rejected sets.

        Args:
            triples: Triples to check against the ontology.

        Returns:
            kept: Triples allowed by at least one rule.
            violations: Rejected triples paired with rejection reasons.
        """
        kept: list[Triple] = []
        violations: list[OntologyViolation] = []
        for triple in triples:
            if self.allows(triple):
                kept.append(triple)
            else:
                reason = (
                    f"no rule allows ({triple.subject.entity_type}, "
                    f"{triple.predicate!r}, {triple.object.entity_type})"
                )
                violations.append(OntologyViolation(triple, reason))
        return kept, violations

    def add_rule(self, rule: OntologyRule) -> "Ontology":
        """Derives a new ontology with one additional rule.

        Args:
            rule: Rule to add to the existing set.

        Returns:
            ontology: New Ontology containing the union of rules.
        """
        return Ontology(set(self.rules) | {rule}, strict=self.strict)

    def merge(self, other: "Ontology") -> "Ontology":
        """Combines two ontologies into their rule union.

        Args:
            other: Ontology whose rules are merged in.

        Returns:
            ontology: New Ontology with the combined rule set.
        """
        return Ontology(set(self.rules) | set(other.rules), strict=self.strict and other.strict)

    @classmethod
    def from_dict(cls, data: list[dict[str, str]], strict: bool = True) -> "Ontology":
        """Builds an ontology from raw rule mappings.

        Args:
            data: Mappings with subject_type, predicate, and object_type keys.
            strict: Whether the resulting ontology rejects unmatched triples.

        Returns:
            ontology: Ontology built from the supplied rules.
        """
        rules = {
            OntologyRule(
                subject_type=entry["subject_type"],
                predicate=entry["predicate"],
                object_type=entry["object_type"],
            )
            for entry in data
        }
        return cls(rules, strict=strict)

    def to_dict(self) -> list[dict[str, str]]:
        """Serializes the rule set to plain mappings.

        Returns:
            data: Rule mappings suitable for JSON persistence.
        """
        return [
            {
                "subject_type": rule.subject_type,
                "predicate": rule.predicate,
                "object_type": rule.object_type,
            }
            for rule in sorted(self.rules, key=lambda r: (r.subject_type, r.predicate))
        ]
