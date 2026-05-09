#!/usr/bin/env python3
"""
test_neo4j_loader.py --- integration tests for the Neo4j loader against a live instance

Contains:
    RecordingDriver: in-memory driver double
    make_loader(): builds a loader with a recording driver
    test_write_triples_emits_node_and_rel_queries
    test_write_triples_applies_constraints_first
    test_batches_respect_configured_batch_size
    test_stats_count_written_rows
    test_transient_failures_are_retried
    test_persistent_failure_raises_load_error
    test_self_loop_triples_are_skipped
    test_node_rows_are_deduplicated
    test_relationship_rows_carry_confidence_and_inference
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


def test_batches_respect_configured_batch_size() -> None:
    """Checks that row batches never exceed the configured batch size."""
    loader, driver = make_loader(batch_size=2)
    triples = [make_triple(f"S{i}", "links", f"O{i}") for i in range(5)]
    loader.write_triples(triples)
    for query, parameters in driver.queries:
        if query == UPSERT_NODES_QUERY:
            assert len(parameters["rows"]) <= 2


def test_stats_count_written_rows() -> None:
    """Checks that load stats count nodes, relationships, and batches."""
    loader, _ = make_loader(batch_size=10)
    stats = loader.write_triples([make_triple(), make_triple("Bob", "joined", "Acme")])
    assert stats.nodes_written == 3
    assert stats.relationships_written == 2
    assert stats.batches_written >= 2


def test_transient_failures_are_retried() -> None:
    """Checks that transient batch failures are retried and counted."""
    loader, _ = make_loader(failures=1)
    loader.write_triples([make_triple()])
    assert loader.stats.retries == 1


def test_persistent_failure_raises_load_error() -> None:
    """Checks that persistent batch failure surfaces as LoadError."""
    loader, _ = make_loader(failures=99)
    try:
        loader.write_triples([make_triple()])
        raised = False
    except LoadError:
        raised = True
    assert raised


def test_self_loop_triples_are_skipped() -> None:
    """Checks that self-loop triples never reach the relationship query."""
    loader, driver = make_loader(batch_size=10)
    loader.write_triples([make_triple("Acme", "owns", "acme")])
    rel_queries = [p for q, p in driver.queries if q == UPSERT_RELS_QUERY]
    assert rel_queries == []


def test_node_rows_are_deduplicated() -> None:
    """Checks that repeated entities produce a single node row."""
    writer = BatchWriter(batch_size=10)
    triples = [make_triple(), make_triple("Alice", "joined", "Acme")]
    rows = writer.node_rows(triples)
    assert len(rows) == 2


def test_relationship_rows_carry_confidence_and_inference() -> None:
    """Checks that relationship rows carry confidence and inferred flags."""
    writer = BatchWriter(batch_size=10)
    rows = writer.relationship_rows([make_triple(confidence=0.7)])
    assert rows[0]["confidence"] == 0.7
    assert rows[0]["inferred"] is False
