#!/usr/bin/env python3
"""
ontology.py --- ontology rules and schema enforcement for extracted triples

Contains:
    OntologyRule: one allowed subject-predicate-object type pattern
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
