#!/usr/bin/env python3
"""
test_relationship_inference.py --- unit tests for relationship inference between subgraphs

Contains:
    test_connected_graph_yields_no_bridges
    test_disconnected_components_are_bridged
"""

from extract.relationship_inference import (
    InferenceConfig,
    RelationshipInferer,
    component_report,
    merge_inferred,
)
from tests.unit.factories import make_triple, make_triple_chain


def test_connected_graph_yields_no_bridges() -> None:
    """Checks that a fully connected graph needs no bridges."""
    triples = make_triple_chain(["a", "b", "c"])
    assert RelationshipInferer().infer(triples) == []


def test_disconnected_components_are_bridged() -> None:
    """Checks that disconnected components produce inferred bridges."""
    triples = make_triple_chain(["alpha", "beta"]) + make_triple_chain(["gamma", "delta"])
    bridges = RelationshipInferer().infer(triples)
    assert bridges
    assert all(triple.inferred for triple in bridges)
