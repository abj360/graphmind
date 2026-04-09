#!/usr/bin/env python3
"""
schema.py --- pydantic models and validation helpers for extracted SPO triples

Contains:
    SourceSpan: character offsets anchoring a triple to its source text
    SourceSpan.end_after_start(): rejects zero-length or inverted spans
    EntityRef: one endpoint of an SPO triple
    EntityRef.normalized_name(): case-folded comparison key
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
