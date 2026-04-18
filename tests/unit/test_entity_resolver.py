#!/usr/bin/env python3
"""
test_entity_resolver.py --- unit tests for embedding-based entity resolution

Contains:
"""

from resolution.entity_resolver import EntityResolver, resolve_names, summarize_merges
from tests.unit.factories import make_triple
