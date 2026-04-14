#!/usr/bin/env python3
"""
test_neo4j_loader.py --- integration tests for the Neo4j loader against a live instance

Contains:
"""

from typing import Any

from load.batch_writer import BatchWriter, batched, count_batches, estimate_write_seconds
from load.neo4j_loader import (
    UPSERT_NODES_QUERY,
    UPSERT_RELS_QUERY,
    LoadConfig,
    LoadError,
    LoadStats,
    Neo4jLoader,
    TransientWriteError,
    format_load_stats,
)
from tests.unit.factories import make_triple
