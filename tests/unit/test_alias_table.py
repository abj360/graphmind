#!/usr/bin/env python3
"""
test_alias_table.py --- unit tests for the alias table and merge review queue

Contains:
"""

import pytest

from resolution.alias_table import (
    AliasTable,
    MergeReviewQueue,
    ReviewItem,
    apply_decisions,
    load_alias_table,
    queue_from_borderline,
    save_alias_table,
)
