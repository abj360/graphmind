#!/usr/bin/env python3
"""
test_relationship_inference.py --- unit tests for relationship inference between subgraphs

Contains:
"""

from extract.relationship_inference import (
    InferenceConfig,
    RelationshipInferer,
    component_report,
    merge_inferred,
)
from tests.unit.factories import make_triple, make_triple_chain
