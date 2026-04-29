#!/usr/bin/env python3
"""
batch_writer.py --- converts resolved triples into batched UNWIND row payloads

Contains:
    DEFAULT_BATCH_SIZE: rows per UNWIND batch by default
    BatchMetrics: counters for batch preparation
    BatchWriter: slices triples into batched write payloads
    BatchWriter.node_rows(): deduplicated node rows from triples
    BatchWriter.relationship_rows(): rows from non-self-loop triples
    BatchWriter.node_batches(): yields node row batches
    BatchWriter.relationship_batches(): yields relationship batches
    batched(): slices a list into fixed-size batches
    count_batches(): reports how many batches rows would make
    node_row(): builds one node row from entity parts
    relationship_row(): builds one relationship row from a triple
    estimate_write_seconds(): rough wall-clock write estimate
    row_size_bytes(): approximates payload size of one row
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

    def node_rows(self, triples: list[Triple]) -> list[dict[str, Any]]:
        """Builds deduplicated node rows from a triple set.

        Args:
            triples: Triples whose endpoints become node rows.

        Returns:
            rows: One row per distinct entity name.
        """
        rows: dict[str, dict[str, Any]] = {}
        for triple in triples:
            for entity in (triple.subject, triple.object):
                rows.setdefault(
                    entity.name, node_row(entity.name, entity.entity_type, triple.source_doc_id)
                )
        self.metrics.node_rows = len(rows)
        return list(rows.values())

    def relationship_rows(self, triples: list[Triple]) -> list[dict[str, Any]]:
        """Builds relationship rows, skipping degenerate self-loops.

        Args:
            triples: Triples to convert into relationship rows.

        Returns:
            rows: One row per non-self-loop triple.
        """
        rows: list[dict[str, Any]] = []
        skipped = 0
        for triple in triples:
            if triple.subject.normalized_name() == triple.object.normalized_name():
                skipped += 1
                continue
            rows.append(relationship_row(triple))
        self.metrics.relationship_rows = len(rows)
        self.metrics.skipped_self_loops = skipped
        return rows

    def node_batches(self, triples: list[Triple]) -> Iterator[list[dict[str, Any]]]:
        """Yields deduplicated node rows in fixed-size batches.

        Args:
            triples: Triples whose endpoints become node rows.

        Yields:
            batch: Node row lists of at most batch_size entries.
        """
        yield from batched(self.node_rows(triples), self.batch_size)

    def relationship_batches(self, triples: list[Triple]) -> Iterator[list[dict[str, Any]]]:
        """Yields relationship rows in fixed-size batches.

        Args:
            triples: Triples to convert into relationship rows.

        Yields:
            batch: Relationship row lists of at most batch_size entries.
        """
        yield from batched(self.relationship_rows(triples), self.batch_size)


def batched(rows: list[dict[str, Any]], size: int) -> Iterator[list[dict[str, Any]]]:
    """Slices a row list into batches of at most size entries.

    Args:
        rows: Rows to slice.
        size: Maximum rows per batch.

    Yields:
        batch: Row lists of at most size entries.
    """
    for index in range(0, len(rows), size):
        yield rows[index : index + size]


def count_batches(row_count: int, size: int) -> int:
    """Reports how many batches a row count produces at a batch size.

    Args:
        row_count: Total rows to write.
        size: Maximum rows per batch.

    Returns:
        count: Number of batches needed.
    """
    if size < 1:
        msg = f"batch size {size} must be at least 1"
        raise ValueError(msg)
    return -(-row_count // size)


def node_row(name: str, entity_type: str, doc_id: str) -> dict[str, Any]:
    """Builds one node upsert row from entity parts.

    Args:
        name: Canonical entity name.
        entity_type: Coarse entity type label.
        doc_id: Document the entity was last seen in.

    Returns:
        row: Mapping matching the UNWIND node payload shape.
    """
    return {"name": name, "entity_type": entity_type, "doc_id": doc_id}


def relationship_row(triple: Triple) -> dict[str, Any]:
    """Builds one relationship upsert row from a triple.

    Args:
        triple: Triple to convert.

    Returns:
        row: Mapping matching the UNWIND relationship payload shape.
    """
    return {
        "subject": triple.subject.name,
        "object": triple.object.name,
        "predicate": triple.predicate,
        "confidence": triple.confidence,
        "doc_id": triple.source_doc_id,
        "inferred": triple.inferred,
    }


def estimate_write_seconds(row_count: int, size: int, seconds_per_batch: float = 0.12) -> float:
    """Estimates wall-clock seconds needed to write a row volume.

    Args:
        row_count: Total rows to write.
        size: Maximum rows per batch.
        seconds_per_batch: Observed per-batch latency.

    Returns:
        estimate: Approximate total write duration in seconds.
    """
    return count_batches(row_count, size) * seconds_per_batch


def row_size_bytes(row: dict[str, Any]) -> int:
    """Approximates the serialized size of one row payload.

    Args:
        row: Row payload to measure.

    Returns:
        size: Approximate byte size of the serialized row.
    """
    return sum(len(str(key)) + len(str(value)) for key, value in row.items())
