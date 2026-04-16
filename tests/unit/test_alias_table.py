#!/usr/bin/env python3
"""
test_alias_table.py --- unit tests for the alias table and merge review queue

Contains:
    make_item(): concise review item factory
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


def make_item(
    item_id: str = "review-1", canonical: str = "acme", alias: str = "acme corp"
) -> ReviewItem:
    """Builds a review item with overridable defaults.

    Args:
        item_id: Stable identifier for the item.
        canonical: Proposed canonical name.
        alias: Proposed alias.

    Returns:
        item: Review item for queue tests.
    """
    return ReviewItem(item_id=item_id, canonical=canonical, alias=alias, similarity=0.8)
