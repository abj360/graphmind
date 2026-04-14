#!/usr/bin/env python3
"""
conftest.py --- shared fixtures for integration tests against Neo4j

Contains:
    neo4j_available(): skips when no Neo4j is reachable
    neo4j_config fixture
    loader fixture
"""

import os

import pytest


def neo4j_available() -> bool:
    """Reports whether an integration Neo4j instance is configured.

    Returns:
        available: True when GRAPHMIND_TEST_NEO4J_URI is set.
    """
    return bool(os.environ.get("GRAPHMIND_TEST_NEO4J_URI"))


@pytest.fixture
def neo4j_config():
    """Provides the integration Neo4j connection config, skipping if absent.

    Returns:
        config: LoadConfig pointing at the test instance.
    """
    if not neo4j_available():
        pytest.skip("GRAPHMIND_TEST_NEO4J_URI not set; skipping integration test")
    from load.neo4j_loader import LoadConfig

    return LoadConfig(
        uri=os.environ["GRAPHMIND_TEST_NEO4J_URI"],
        user=os.environ.get("GRAPHMIND_TEST_NEO4J_USER", "neo4j"),
        password=os.environ.get("GRAPHMIND_TEST_NEO4J_PASSWORD", "graphmind-dev"),
    )


@pytest.fixture
def loader(neo4j_config):
    """Provides a connected Neo4jLoader bound to the test instance.

    Args:
        neo4j_config: Connection config fixture.

    Yields:
        loader: Connected loader, closed after the test.
    """
    from load.neo4j_loader import Neo4jLoader

    with Neo4jLoader(neo4j_config) as instance:
        yield instance
