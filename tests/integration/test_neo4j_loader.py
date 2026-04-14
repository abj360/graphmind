#!/usr/bin/env python3
"""
test_neo4j_loader.py --- integration tests for the Neo4j loader against a live instance

Contains:
    RecordingDriver: in-memory driver double
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


class RecordingDriver:
    """Records executed queries instead of talking to Neo4j.

    Attributes:
        queries: (query, parameters) pairs executed so far.
        failures_remaining: Calls that still raise TransientWriteError.
    """

    def __init__(self, failures: int = 0) -> None:
        """Creates a recording driver with optional transient failures.

        Args:
            failures: Number of calls that raise before succeeding.
        """
        self.queries: list[tuple[str, dict[str, Any]]] = []
        self.failures_remaining = failures
        self.closed = False

    def execute_query(self, query: str, parameters: dict[str, Any], database: str) -> None:
        """Records one query, raising while failures remain.

        Args:
            query: Cypher statement to record.
            parameters: Query parameters to record.
            database: Target database name, recorded implicitly.
        """
        if self.failures_remaining > 0 and "UNWIND" in query:
            self.failures_remaining -= 1
            raise TransientWriteError("simulated transient failure")
        self.queries.append((query, parameters))

    def close(self) -> None:
        """Marks the driver as closed."""
        self.closed = True
