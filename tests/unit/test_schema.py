#!/usr/bin/env python3
"""
test_schema.py --- unit tests for triple schema validation

Contains:
"""

import pytest

from extract.schema import (
    SourceSpan,
    TripleValidationError,
    clamp_confidence,
    confidence_stats,
    dedupe_triples,
    filter_by_confidence,
    validate_triple,
    validate_triples,
    validate_triples_strict,
)
from tests.unit.factories import make_triple
