#!/usr/bin/env python3
"""
batch_writer.py --- converts resolved triples into batched UNWIND row payloads

Contains:
    DEFAULT_BATCH_SIZE: rows per UNWIND batch by default
    BatchMetrics: counters for batch preparation
    BatchWriter: slices triples into batched write payloads
"""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from extract.schema import Triple

DEFAULT_BATCH_SIZE = 500


@dataclass
class BatchMetrics:
    """Tracks counters describing batch preparation.

    Attributes:
        node_rows: Node rows produced.
        relationship_rows: Relationship rows produced.
        skipped_self_loops: Triples dropped because subject equals object.
    """

    node_rows: int = 0
    relationship_rows: int = 0
    skipped_self_loops: int = 0


class BatchWriter:
    """Converts triples into batched node and relationship row payloads.

    Attributes:
        batch_size: Maximum rows per yielded batch.
        metrics: Mutable counters for the last prepared run.
    """

    def __init__(self, batch_size: int = DEFAULT_BATCH_SIZE) -> None:
        """Creates a batch writer with a fixed batch size.

        Args:
            batch_size: Maximum rows per yielded batch.
        """
        if batch_size < 1:
            msg = f"batch_size {batch_size} must be at least 1"
            raise ValueError(msg)
        self.batch_size = batch_size
        self.metrics = BatchMetrics()
