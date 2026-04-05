#!/usr/bin/env python3
"""
conftest.py --- shared fixtures for integration tests against Neo4j

Contains:
    neo4j_available(): skips when no Neo4j is reachable
"""

import os

import pytest


def neo4j_available() -> bool:
    """Reports whether an integration Neo4j instance is configured.

    Returns:
        available: True when GRAPHMIND_TEST_NEO4J_URI is set.
    """
    return bool(os.environ.get("GRAPHMIND_TEST_NEO4J_URI"))
