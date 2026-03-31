#!/usr/bin/env python3
"""
schema.py --- pydantic models and validation helpers for extracted SPO triples

Contains:
    SourceSpan: character offsets anchoring a triple to its source text
    SourceSpan.end_after_start(): rejects zero-length or inverted spans
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
