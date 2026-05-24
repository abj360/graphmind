#!/usr/bin/env python3
"""
test_relationship_inference.py --- unit tests for relationship inference between subgraphs

Contains:
    test_connected_graph_yields_no_bridges
    test_disconnected_components_are_bridged
    test_low_confidence_bridges_are_filtered
    test_component_report_counts_components
    test_merge_inferred_dedupes_existing_edges
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


def test_low_confidence_bridges_are_filtered() -> None:
    """Checks that a high confidence floor suppresses weak bridges."""
    triples = make_triple_chain(["alpha", "beta"]) + make_triple_chain(["gamma", "delta"])
    inferer = RelationshipInferer(InferenceConfig(min_bridge_confidence=0.99))
    assert inferer.infer(triples) == []


def test_component_report_counts_components() -> None:
    """Checks that the component report tallies components and entities."""
    triples = make_triple_chain(["a", "b", "c"]) + make_triple_chain(["x", "y"])
    report = component_report(triples)
    assert report["components"] == 2
    assert report["entities"] == 5


def test_merge_inferred_dedupes_existing_edges() -> None:
    """Checks that merging inferred triples never duplicates an edge."""
    extracted = [make_triple("Alice", "founded", "Acme")]
    duplicate = make_triple("Alice", "founded", "Acme", confidence=0.5)
    inferred = [duplicate.model_copy(update={"inferred": True})]
    assert len(merge_inferred(extracted, inferred)) == 1
