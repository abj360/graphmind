#!/usr/bin/env python3
"""
__init__.py --- LLM-based extraction of SPO triples from raw text

Contains:
    __all__: public surface of the extract package
"""

from extract.schema import EntityRef, SourceSpan, Triple

__all__ = [
    "EntityRef",
    "SourceSpan",
    "Triple",
]
