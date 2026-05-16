#!/usr/bin/env python3
"""
test_ontology.py --- unit tests for ontology schema enforcement

Contains:
"""

from extract.ontology import (
    Ontology,
    OntologyRule,
    diff_ontologies,
    infer_rules,
)
from tests.unit.factories import make_triple
