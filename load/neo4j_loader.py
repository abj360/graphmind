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
"""

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Protocol

from extract.schema import Triple

logger = logging.getLogger(__name__)

SINGLE_NODE_QUERY = """
MERGE (n:Entity {name: $name})
SET n.entity_type = $entity_type,
    n.last_seen_doc = $doc_id
""".strip()

SINGLE_REL_QUERY = """
MATCH (s:Entity {name: $subject})
MATCH (o:Entity {name: $object})
MERGE (s)-[r:RELATED {predicate: $predicate}]->(o)
SET r.confidence = $confidence,
    r.source_doc_id = $doc_id
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
