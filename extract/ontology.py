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
    Ontology.coverage(): share of triples the ontology allows
    Ontology.summary(): counts rules by subject type
    load_ontology(): reads an ontology from a JSON file
    default_rules(): built-in starter rule set
    load_default_ontology(): ontology from the built-in rules
    infer_rules(): mines candidate rules from trusted triples
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

    def coverage(self, triples: list[Triple]) -> float:
        """Computes the share of triples allowed by the ontology.

        Args:
            triples: Triples to measure coverage over.

        Returns:
            coverage: Fraction of triples allowed, between 0 and 1.
        """
        if not triples:
            return 1.0
        allowed = sum(1 for triple in triples if self.allows(triple))
        return allowed / len(triples)

    def summary(self) -> dict[str, int]:
        """Counts how many rules exist per subject type.

        Returns:
            counts: Mapping of subject type to rule count.
        """
        counts: dict[str, int] = {}
        for rule in self.rules:
            counts[rule.subject_type] = counts.get(rule.subject_type, 0) + 1
        return counts


def load_ontology(path: Path, strict: bool = True) -> Ontology:
    """Reads an ontology definition from a JSON file.

    Args:
        path: JSON file containing a list of rule mappings.
        strict: Whether the loaded ontology rejects unmatched triples.

    Returns:
        ontology: Ontology parsed from the file.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        msg = f"ontology file {path} must contain a JSON array"
        raise ValueError(msg)
    return Ontology.from_dict(data, strict=strict)


def default_rules() -> set[OntologyRule]:
    """Provides the built-in starter ontology rule set.

    Returns:
        rules: Seed rules covering common entity-type combinations.
    """
    return {
        OntologyRule("PERSON", "founded", "ORG"),
        OntologyRule("PERSON", "joined", "ORG"),
        OntologyRule("PERSON", "works at", "ORG"),
        OntologyRule("ORG", "acquired", "ORG"),
        OntologyRule("ORG", "is based in", "GPE"),
        OntologyRule("SOFTWARE", "depends on", "SOFTWARE"),
        OntologyRule("SOFTWARE", "ships with", "SOFTWARE"),
        OntologyRule("SOFTWARE", "configures", "SOFTWARE"),
        OntologyRule("DRUG", "inhibits", "GENE"),
        OntologyRule("GENE", "mutates in", "DISEASE"),
    }


def load_default_ontology(strict: bool = True) -> Ontology:
    """Builds the default ontology from the built-in rule set.

    Args:
        strict: Whether the ontology rejects unmatched triples.

    Returns:
        ontology: Ontology seeded with the default rules.
    """
    return Ontology(default_rules(), strict=strict)


def infer_rules(triples: list[Triple]) -> set[OntologyRule]:
    """Mines candidate ontology rules from a set of trusted triples.

    Args:
        triples: Trusted triples whose type patterns become rules.

    Returns:
        rules: Distinct observed (type, predicate, type) patterns.
    """
    return {OntologyRule(t.subject.entity_type, t.predicate, t.object.entity_type) for t in triples}
