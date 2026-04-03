#!/usr/bin/env python3
"""
conftest.py --- shared fixtures for unit tests

Contains:
    triple_factory fixture
    sample_triples fixture
"""

import pytest

from extract.schema import Triple
from tests.unit.factories import make_triple


@pytest.fixture
def triple_factory():
    """Provides the make_triple factory as a fixture.

    Returns:
        factory: The make_triple function.
    """
    return make_triple


@pytest.fixture
def sample_triples() -> list[Triple]:
    """Provides a small connected triple set for graph tests.

    Returns:
        triples: Four triples forming one connected component.
    """
    return [
        make_triple("Alice", "founded", "Acme"),
        make_triple("Acme", "acquired", "ByteWorks", subject_type="ORG"),
        make_triple("ByteWorks", "is based in", "Leeds", subject_type="ORG", object_type="GPE"),
        make_triple("Bob", "joined", "Acme"),
    ]
