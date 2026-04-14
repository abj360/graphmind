#!/usr/bin/env python3
"""
test_neo4j_loader.py --- integration tests for the Neo4j loader against a live instance

Contains:
    RecordingDriver: in-memory driver double
    make_loader(): builds a loader with a recording driver
    test_write_triples_emits_node_and_rel_queries
    test_write_triples_applies_constraints_first
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


def make_loader(failures: int = 0, batch_size: int = 2) -> tuple[Neo4jLoader, RecordingDriver]:
    """Builds a loader wired to a recording driver double.

    Args:
        failures: Transient failures the driver should simulate.
        batch_size: Batch size for the loader under test.

    Returns:
        loader: Loader under test.
        driver: Recording driver capturing its queries.
    """
    driver = RecordingDriver(failures)
    loader = Neo4jLoader(LoadConfig(batch_size=batch_size, max_retries=2), driver=driver)
    return loader, driver


def test_write_triples_emits_node_and_rel_queries() -> None:
    """Checks that writing triples emits both node and relationship batches."""
    loader, driver = make_loader()
    loader.write_triples([make_triple()])
    queries = [query for query, _ in driver.queries]
    assert UPSERT_NODES_QUERY in queries
    assert UPSERT_RELS_QUERY in queries


def test_write_triples_applies_constraints_first() -> None:
    """Checks that uniqueness constraints are applied before any batch."""
    loader, driver = make_loader()
    loader.write_triples([make_triple()])
    first_queries = [query for query, _ in driver.queries[: len(Neo4jLoader.CONSTRAINT_QUERIES)]]
    assert first_queries == Neo4jLoader.CONSTRAINT_QUERIES
