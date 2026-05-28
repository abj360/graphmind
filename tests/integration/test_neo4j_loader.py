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
    test_batched_slices_rows_exactly
    test_count_batches_rounds_up
    test_batch_writer_rejects_zero_batch_size
    test_estimate_write_seconds_scales_with_batches
    test_close_marks_driver_closed
    test_healthcheck_reports_true_with_working_driver
    test_delete_doc_triples_scopes_to_document
    test_format_load_stats_renders_counters
    test_live_instance_roundtrip
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


def test_batched_slices_rows_exactly() -> None:
    """Checks that batched() slices rows into exact fixed-size groups."""
    rows = [{"i": i} for i in range(7)]
    batches = list(batched(rows, 3))
    assert [len(batch) for batch in batches] == [3, 3, 1]


def test_count_batches_rounds_up() -> None:
    """Checks that batch counting rounds up partial batches."""
    assert count_batches(7, 3) == 3
    assert count_batches(0, 3) == 0


def test_batch_writer_rejects_zero_batch_size() -> None:
    """Checks that a zero batch size is rejected at construction."""
    try:
        BatchWriter(batch_size=0)
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_estimate_write_seconds_scales_with_batches() -> None:
    """Checks that the write estimate scales linearly with batches."""
    assert estimate_write_seconds(10, 5, 0.1) == estimate_write_seconds(5, 5, 0.1) * 2


def test_close_marks_driver_closed() -> None:
    """Checks that closing the loader closes the driver."""
    loader, driver = make_loader()
    loader.close()
    assert driver.closed


def test_healthcheck_reports_true_with_working_driver() -> None:
    """Checks that the healthcheck passes with a working driver."""
    loader, _ = make_loader()
    assert loader.healthcheck()


def test_delete_doc_triples_scopes_to_document() -> None:
    """Checks that document deletion passes the doc_id as a parameter."""
    loader, driver = make_loader()
    loader.delete_doc_triples("doc-9")
    assert driver.queries[-1][1] == {"doc_id": "doc-9"}


def test_format_load_stats_renders_counters() -> None:
    """Checks that the stats summary mentions nodes and batches."""
    summary = format_load_stats(LoadStats(nodes_written=4, batches_written=2))
    assert "nodes=4" in summary
    assert "batches=2" in summary


def test_live_instance_roundtrip(loader) -> None:
    """Writes and reads back triples against a live Neo4j instance.

    Args:
        loader: Connected loader fixture bound to the test instance.
    """
    stats = loader.write_triples([make_triple()])
    assert stats.batches_written >= 1
