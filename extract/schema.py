#!/usr/bin/env python3
"""
schema.py --- pydantic models and validation helpers for extracted SPO triples

Contains:
    SourceSpan: character offsets anchoring a triple to its source text
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
