#!/usr/bin/env python3
"""
test_alias_table.py --- unit tests for the alias table and merge review queue

Contains:
    make_item(): concise review item factory
    test_add_and_resolve_alias
    test_unknown_name_resolves_to_itself
    test_aliases_lists_registered_aliases
    test_self_alias_is_not_registered
    test_merge_remaps_aliases_to_survivor
    test_merge_same_canonical_is_noop
    test_save_and_load_alias_table
    test_load_missing_file_yields_empty_table
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


def test_add_and_resolve_alias() -> None:
    """Checks that a registered alias resolves to its canonical name."""
    table = AliasTable()
    table.add("Acme", "ACME Corp")
    assert table.canonical_for("acme corp") == "acme"


def test_unknown_name_resolves_to_itself() -> None:
    """Checks that unregistered names normalize but pass through."""
    table = AliasTable()
    assert table.canonical_for("Globex Inc") == "globex inc"


def test_aliases_lists_registered_aliases() -> None:
    """Checks that aliases() enumerates everything under a canonical."""
    table = AliasTable()
    table.add("Acme", "ACME Corp")
    table.add("Acme", "Acme Incorporated")
    assert table.aliases("Acme") == ["acme corp", "acme incorporated"]


def test_self_alias_is_not_registered() -> None:
    """Checks that aliasing a name to itself is a no-op."""
    table = AliasTable()
    table.add("Acme", "acme")
    assert table.aliases("Acme") == []


def test_merge_remaps_aliases_to_survivor() -> None:
    """Checks that merging canonicals remaps all aliases to the survivor."""
    table = AliasTable()
    table.add("Acme", "ACME Corp")
    table.merge("Acme Ltd", "Acme")
    assert table.canonical_for("acme corp") == "acme ltd"
    assert table.canonical_for("acme") == "acme ltd"


def test_merge_same_canonical_is_noop() -> None:
    """Checks that merging a canonical into itself changes nothing."""
    table = AliasTable()
    table.add("Acme", "ACME Corp")
    table.merge("Acme", "acme")
    assert table.canonical_for("acme corp") == "acme"


def test_save_and_load_alias_table(tmp_path) -> None:
    """Checks that JSON persistence round-trips the table."""
    path = tmp_path / "aliases.json"
    table = AliasTable()
    table.add("Acme", "ACME Corp")
    save_alias_table(table, path)
    assert load_alias_table(path).canonical_for("acme corp") == "acme"


def test_load_missing_file_yields_empty_table(tmp_path) -> None:
    """Checks that loading a missing file yields an empty table."""
    table = load_alias_table(tmp_path / "missing.json")
    assert table.to_dict() == {}
