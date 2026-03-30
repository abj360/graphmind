#!/usr/bin/env python3
"""
neo4j_loader.py --- batched, upsert-only writer loading triples into Neo4j

Contains:
    logger + query constants
    UPSERT_NODES_QUERY: MERGE-based node upsert statement
    UPSERT_RELS_QUERY: MERGE-based relationship upsert statement
    LoadConfig: connection and batching configuration
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
