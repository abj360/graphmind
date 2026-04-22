#!/usr/bin/env python3
"""
factories.py --- shared test data builders for unit tests

Contains:
    make_triple(): concise triple factory for tests
    make_triple_chain(): builds a connected chain of triples
    make_raw_item(): raw LLM payload factory
"""

from extract.schema import EntityRef, Triple


def make_triple(
    subject: str = "Alice",
    predicate: str = "founded",
    object_: str = "Acme",
    confidence: float = 0.9,
    doc_id: str = "doc-1",
    subject_type: str = "PERSON",
    object_type: str = "ORG",
) -> Triple:
    """Builds a valid triple with overridable defaults.

    Args:
        subject: Subject entity name.
        predicate: Predicate phrase.
        object_: Object entity name.
        confidence: Confidence score.
        doc_id: Source document identifier.
        subject_type: Subject entity type.
        object_type: Object entity type.

    Returns:
        triple: Validated test triple.
    """
    return Triple(
        subject=EntityRef(name=subject, entity_type=subject_type),
        predicate=predicate,
        object=EntityRef(name=object_, entity_type=object_type),
        confidence=confidence,
        source_doc_id=doc_id,
    )


def make_triple_chain(names: list[str], predicate: str = "links") -> list[Triple]:
    """Builds a chain of triples linking consecutive names.

    Args:
        names: Entity names to link in order.
        predicate: Predicate phrase used for every link.

    Returns:
        triples: len(names) - 1 triples forming one chain.
    """
    from itertools import pairwise

    return [
        make_triple(left, predicate, right, subject_type="CONCEPT", object_type="CONCEPT")
        for left, right in pairwise(names)
    ]


def make_raw_item(
    subject: str = "Alice",
    predicate: str = "founded",
    object_: str = "Acme",
    confidence: float = 0.9,
) -> dict:
    """Builds a raw extractor payload dict with overridable defaults.

    Args:
        subject: Subject entity name.
        predicate: Predicate phrase.
        object_: Object entity name.
        confidence: Confidence score.

    Returns:
        item: Raw mapping shaped like parsed LLM output.
    """
    return {
        "subject": {"name": subject, "entity_type": "PERSON"},
        "predicate": predicate,
        "object": {"name": object_, "entity_type": "ORG"},
        "confidence": confidence,
    }
