#!/usr/bin/env python3
"""
schema.py --- pydantic models and validation helpers for extracted SPO triples

Contains:
    SourceSpan: character offsets anchoring a triple to its source text
    SourceSpan.end_after_start(): rejects zero-length or inverted spans
    EntityRef: one endpoint of an SPO triple
    EntityRef.normalized_name(): case-folded comparison key
    Triple: one validated subject-predicate-object fact
    Triple.key(): deduplication identity tuple
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceSpan(BaseModel):
    """Locates the exact passage a triple was extracted from.

    Attributes:
        start: Inclusive character offset of the cited passage.
        end: Exclusive character offset of the cited passage.
        text: Verbatim cited passage from the source document.
    """

    model_config = ConfigDict(frozen=True)

    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str = Field(min_length=1)

    @field_validator("end")
    @classmethod
    def end_after_start(cls, value: int, info: Any) -> int:
        """Validates that the span end is strictly greater than its start.

        Args:
            value: Candidate end offset.
            info: Pydantic validation context carrying sibling field values.

        Returns:
            value: The accepted end offset.
        """
        start = info.data.get("start")
        if start is not None and value <= start:
            msg = f"span end {value} must be greater than start {start}"
            raise ValueError(msg)
        return value


class EntityRef(BaseModel):
    """Represents a named entity participating in a triple.

    Attributes:
        name: Surface form of the entity as seen in the source text.
        entity_type: Coarse type label such as PERSON, ORG, or CONCEPT.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    entity_type: str = Field(default="CONCEPT", min_length=1)

    @field_validator("name", "entity_type")
    @classmethod
    def strip_and_check(cls, value: str) -> str:
        """Normalizes whitespace and rejects blank values.

        Args:
            value: Raw field value supplied by the extractor.

        Returns:
            value: Trimmed, non-empty field value.
        """
        cleaned = value.strip()
        if not cleaned:
            msg = "entity fields must not be blank"
            raise ValueError(msg)
        return cleaned

    def normalized_name(self) -> str:
        """Computes the case-folded comparison key for this entity.

        Returns:
            key: Lowercased, whitespace-collapsed entity name.
        """
        return " ".join(self.name.casefold().split())


class Triple(BaseModel):
    """Represents a single extracted fact with provenance and confidence.

    Attributes:
        subject: Entity the fact is about.
        predicate: Relationship phrase linking subject and object.
        object: Entity the subject is related to.
        confidence: Extractor confidence in the fact, between 0 and 1.
        source_doc_id: Identifier of the document the fact came from.
        source_span: Cited passage supporting the fact, when required.
        inferred: Whether the triple was inferred rather than extracted.
    """

    model_config = ConfigDict(frozen=True)

    subject: EntityRef
    predicate: str = Field(min_length=1)
    object: EntityRef
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_doc_id: str = Field(min_length=1)
    source_span: SourceSpan | None = None
    inferred: bool = False

    @field_validator("predicate")
    @classmethod
    def normalize_predicate(cls, value: str) -> str:
        """Normalizes predicate phrasing to a stable comparable form.

        Args:
            value: Raw predicate phrase from the extractor.

        Returns:
            value: Trimmed predicate with internal whitespace collapsed.
        """
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            msg = "predicate must not be blank"
            raise ValueError(msg)
        return cleaned

    def key(self) -> tuple[str, str, str]:
        """Computes the deduplication key for this triple.

        Returns:
            key: Normalized (subject, predicate, object) identity tuple.
        """
        return (
            self.subject.normalized_name(),
            self.predicate.casefold(),
            self.object.normalized_name(),
        )
