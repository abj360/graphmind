#!/usr/bin/env python3
"""
factories.py --- shared test data builders for unit tests

Contains:
    make_triple(): concise triple factory for tests
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
