#!/usr/bin/env python3
"""
neo4j_loader.py --- batched, upsert-only writer loading triples into Neo4j

Contains:
    logger + query constants
    UPSERT_NODES_QUERY: MERGE-based node upsert statement
    UPSERT_RELS_QUERY: MERGE-based relationship upsert statement
    LoadConfig: connection and batching configuration
    LoadConfig.from_env(): builds config from environment
    LoadStats: counters describing one load run
    TransientWriteError: retryable write failure
    LoadError: unrecoverable load failure
    Neo4jDriver: minimal driver protocol for testability
    Neo4jLoader: upserts triples into Neo4j in batches
    Neo4jLoader.connect(): establishes the driver connection
    Neo4jLoader.close(): releases the driver
    Neo4jLoader.__enter__/__exit__: context manager support
    Neo4jLoader.write_triples(): upserts a triple set
    Neo4jLoader._run(): executes one Cypher statement
    Neo4jLoader._write_batch(): writes one row batch with retries
    Neo4jLoader._record_batch(): updates stats after a batch
    Neo4jLoader.CONSTRAINT_QUERIES: uniqueness constraints
    Neo4jLoader.ensure_constraints(): applies uniqueness constraints
    Neo4jLoader.healthcheck(): verifies connectivity
    Neo4jLoader.delete_doc_triples(): removes a document's facts
    load_triples(): one-shot convenience loader
    format_load_stats(): one-line load summary
    main(): CLI entrypoint for the loader
"""

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, ClassVar, Protocol

from extract.schema import Triple
from load.batch_writer import BatchWriter

logger = logging.getLogger(__name__)

UPSERT_NODES_QUERY = """
UNWIND $rows AS row
MERGE (n:Entity {name: row.name})
SET n.entity_type = row.entity_type,
    n.last_seen_doc = row.doc_id
""".strip()

UPSERT_RELS_QUERY = """
UNWIND $rows AS row
MATCH (s:Entity {name: row.subject})
MATCH (o:Entity {name: row.object})
MERGE (s)-[r:RELATED {predicate: row.predicate}]->(o)
SET r.confidence = row.confidence,
    r.source_doc_id = row.doc_id,
    r.inferred = row.inferred
""".strip()


@dataclass(frozen=True)
class LoadConfig:
    """Carries Neo4j connection and writer configuration.

    Attributes:
        uri: Bolt endpoint of the Neo4j instance.
        user: Username for basic authentication.
        password: Password for basic authentication.
        database: Target database name.
        batch_size: Rows per UNWIND batch.
        max_retries: Attempts per batch before failing the load.
    """

    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "graphmind-dev"
    database: str = "neo4j"
    batch_size: int = 500
    max_retries: int = 3

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "LoadConfig":
        """Builds a LoadConfig from NEO4J_* environment variables.

        Args:
            env: Environment mapping; os.environ is used when omitted.

        Returns:
            config: Connection configuration with overrides applied.
        """
        active = env if env is not None else dict(os.environ)
        return cls(
            uri=active.get("NEO4J_URI", "bolt://localhost:7687"),
            user=active.get("NEO4J_USER", "neo4j"),
            password=active.get("NEO4J_PASSWORD", "graphmind-dev"),
            database=active.get("NEO4J_DATABASE", "neo4j"),
            batch_size=int(active.get("GRAPHMIND_LOAD_BATCH_SIZE", "500")),
        )


@dataclass
class LoadStats:
    """Tracks counters describing one Neo4j load run.

    Attributes:
        nodes_written: Entity rows upserted across all batches.
        relationships_written: Relationship rows upserted across all batches.
        batches_written: Number of batch statements executed.
        retries: Number of batch retries after transient failures.
        duration_seconds: Wall-clock duration of the load.
    """

    nodes_written: int = 0
    relationships_written: int = 0
    batches_written: int = 0
    retries: int = 0
    duration_seconds: float = 0.0


class TransientWriteError(RuntimeError):
    """Marks a write failure that is safe to retry."""


class LoadError(RuntimeError):
    """Raised when a load cannot complete after retries."""


class Neo4jDriver(Protocol):
    """Describes the slice of the neo4j driver the loader uses."""

    def execute_query(self, query: str, parameters: dict[str, Any], database: str) -> None:
        """Executes one Cypher statement with parameters.

        Args:
            query: Cypher statement to run.
            parameters: Query parameters, including the rows payload.
            database: Target database name.
        """
        ...

    def close(self) -> None:
        """Releases driver resources."""
        ...


class Neo4jLoader:
    """Upserts resolved triples into Neo4j using batched UNWIND writes.

    Attributes:
        config: Connection and batching configuration.
        batch_writer: Helper converting triples into row batches.
        stats: Mutable counters for the current or last load.
    """

    def __init__(
        self,
        config: LoadConfig | None = None,
        driver: Neo4jDriver | None = None,
    ) -> None:
        """Creates a loader, optionally with an injected driver for tests.

        Args:
            config: Connection configuration; from_env() when omitted.
            driver: Injected driver double; a real driver is built otherwise.
        """
        self.config = config or LoadConfig.from_env()
        self._driver = driver
        self.batch_writer = BatchWriter(batch_size=self.config.batch_size)
        self.stats = LoadStats()

    def connect(self) -> None:
        """Establishes the Neo4j driver connection if none was injected."""
        if self._driver is not None:
            return
        from neo4j import GraphDatabase  # local import: optional dependency

        self._driver = GraphDatabase.driver(
            self.config.uri, auth=(self.config.user, self.config.password)
        )

    def close(self) -> None:
        """Releases the Neo4j driver connection."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def __enter__(self) -> "Neo4jLoader":
        """Connects on context entry.

        Returns:
            loader: The connected loader instance.
        """
        self.connect()
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Closes the driver on context exit.

        Args:
            exc_info: Exception details supplied by the runtime.
        """
        self.close()

    def write_triples(self, triples: list[Triple]) -> LoadStats:
        """Upserts a set of triples into Neo4j in batches.

        Args:
            triples: Resolved triples to write.

        Returns:
            stats: Counters describing the completed load.
        """
        started = time.monotonic()
        self.connect()
        self.ensure_constraints()
        for node_rows in self.batch_writer.node_batches(triples):
            self._write_batch(UPSERT_NODES_QUERY, node_rows, is_node_batch=True)
        for rel_rows in self.batch_writer.relationship_batches(triples):
            self._write_batch(UPSERT_RELS_QUERY, rel_rows, is_node_batch=False)
        self.stats.duration_seconds = time.monotonic() - started
        return self.stats

    def _run(self, query: str, parameters: dict[str, Any]) -> None:
        """Executes one Cypher statement through the active driver.

        Args:
            query: Cypher statement to run.
            parameters: Query parameters for the statement.
        """
        if self._driver is None:
            raise LoadError("loader is not connected")
        self._driver.execute_query(query, parameters, database=self.config.database)

    def _write_batch(self, query: str, rows: list[dict[str, Any]], is_node_batch: bool) -> None:
        """Writes one batch of rows, retrying transient driver failures.

        Args:
            query: Cypher upsert statement to execute.
            rows: Row payloads for the UNWIND parameter.
            is_node_batch: Whether the batch carries node or relationship rows.
        """
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            try:
                self._run(query, {"rows": rows})
                self._record_batch(rows, is_node_batch)
                return
            except TransientWriteError as exc:
                last_error = exc
                self.stats.retries += 1
                backoff = 0.25 * (attempt + 1)
                logger.warning("batch write failed, retrying in %.2fs: %s", backoff, exc)
                time.sleep(backoff)
        raise LoadError(f"batch write failed after retries: {last_error}")

    def _record_batch(self, rows: list[dict[str, Any]], is_node_batch: bool) -> None:
        """Updates load counters after a successful batch write.

        Args:
            rows: Rows that were just written.
            is_node_batch: Whether the batch carried node or relationship rows.
        """
        self.stats.batches_written += 1
        if is_node_batch:
            self.stats.nodes_written += len(rows)
        else:
            self.stats.relationships_written += len(rows)

    CONSTRAINT_QUERIES: ClassVar[list[str]] = [
        "CREATE CONSTRAINT entity_name_unique IF NOT EXISTS "
        "FOR (n:Entity) REQUIRE n.name IS UNIQUE",
    ]

    def ensure_constraints(self) -> None:
        """Applies the uniqueness constraints the upserts rely on."""
        self.connect()
        for query in self.CONSTRAINT_QUERIES:
            self._run(query, {})

    def healthcheck(self) -> bool:
        """Verifies Neo4j connectivity with a trivial query.

        Returns:
            healthy: True when the instance answers a trivial query.
        """
        try:
            self.connect()
            self._run("RETURN 1 AS ok", {})
            return True
        except (LoadError, OSError) as exc:
            logger.error("neo4j healthcheck failed: %s", exc)
            return False

    def delete_doc_triples(self, doc_id: str) -> None:
        """Removes relationships sourced from one document.

        Args:
            doc_id: Document whose sourced relationships are deleted.
        """
        query = "MATCH ()-[r:RELATED {source_doc_id: $doc_id}]->() DELETE r"
        self._run(query, {"doc_id": doc_id})


def load_triples(triples: list[Triple], config: LoadConfig | None = None) -> LoadStats:
    """Loads triples with a fresh loader, closing it afterwards.

    Args:
        triples: Resolved triples to write.
        config: Connection configuration; from_env() when omitted.

    Returns:
        stats: Counters describing the completed load.
    """
    with Neo4jLoader(config) as loader:
        return loader.write_triples(triples)


def format_load_stats(stats: LoadStats) -> str:
    """Renders load counters as a log-friendly one-liner.

    Args:
        stats: Counters to summarize.

    Returns:
        summary: One-line rendering of rows, batches, and duration.
    """
    return (
        f"nodes={stats.nodes_written} rels={stats.relationships_written} "
        f"batches={stats.batches_written} retries={stats.retries} "
        f"took={stats.duration_seconds:.2f}s"
    )


def main(argv: list[str] | None = None) -> int:
    """Runs the loader CLI over a resolved-triples JSONL file.

    Args:
        argv: Command-line arguments; sys.argv when omitted.

    Returns:
        exit_code: 0 on success, nonzero on failure.
    """
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Load resolved triples into Neo4j")
    parser.add_argument("--input", required=True, help="resolved triples JSONL path")
    args = parser.parse_args(argv)
    triples = []
    for line in Path(args.input).read_text(encoding="utf-8").splitlines():
        if line.strip():
            triples.append(Triple.model_validate(json.loads(line)))
    stats = load_triples(triples)
    logger.info("%s", format_load_stats(stats))
    return 0
