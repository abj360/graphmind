#!/usr/bin/env python3
"""
alias_table.py --- alias table and human-in-the-loop merge review queue

Contains:
    AliasTable: canonical name to known aliases mapping
    AliasTable.add(): registers one alias under a canonical name
    AliasTable.canonical_for(): resolves an alias to its canonical
    AliasTable.aliases(): lists aliases of a canonical name
    AliasTable._normalize(): shared key normalization
    AliasTable.merge(): folds one canonical into another
    AliasTable.to_dict(): serializes the table
    save_alias_table(): persists the table as JSON
    load_alias_table(): restores a table from JSON
    ReviewItem: one pending human merge decision
    MergeReviewQueue: human-in-the-loop merge decision queue
    MergeReviewQueue.submit(): enqueues a borderline candidate
    MergeReviewQueue.approve(): accepts a pending merge
    MergeReviewQueue.reject(): declines a pending merge
    MergeReviewQueue._take(): pops an item by id
"""

import json
from dataclasses import dataclass, field
from pathlib import Path


class AliasTable:
    """Maps canonical entity names to their known aliases.

    Attributes:
        canonical_of: Alias-to-canonical lookup, normalized on write.
    """

    def __init__(self) -> None:
        """Creates an empty alias table."""
        self.canonical_of: dict[str, str] = {}

    def add(self, canonical: str, alias: str) -> None:
        """Registers one alias under a canonical entity name.

        Args:
            canonical: Representative entity name.
            alias: Alternative surface form for the same entity.
        """
        key = self._normalize(alias)
        canonical_key = self._normalize(canonical)
        if key != canonical_key:
            self.canonical_of[key] = canonical_key

    def canonical_for(self, name: str) -> str:
        """Resolves a name to its canonical representative.

        Args:
            name: Surface form to resolve.

        Returns:
            canonical: Registered canonical form, or the normalized input.
        """
        return self.canonical_of.get(self._normalize(name), self._normalize(name))

    def aliases(self, canonical: str) -> list[str]:
        """Lists every alias registered under a canonical name.

        Args:
            canonical: Canonical name whose aliases are listed.

        Returns:
            aliases: Sorted alias keys registered for the canonical name.
        """
        canonical_key = self._normalize(canonical)
        return sorted(
            alias for alias, target in self.canonical_of.items() if target == canonical_key
        )

    @staticmethod
    def _normalize(name: str) -> str:
        """Folds a name into the table's comparison key form.

        Args:
            name: Raw entity surface form.

        Returns:
            key: Case-folded, whitespace-collapsed comparison key.
        """
        return " ".join(name.casefold().split())

    def merge(self, keep: str, drop: str) -> None:
        """Folds one canonical entry into another, remapping its aliases.

        Args:
            keep: Canonical name that survives the merge.
            drop: Canonical name folded into the survivor.
        """
        keep_key = self._normalize(keep)
        drop_key = self._normalize(drop)
        if keep_key == drop_key:
            return
        self.canonical_of[drop_key] = keep_key
        for alias, target in list(self.canonical_of.items()):
            if target == drop_key:
                self.canonical_of[alias] = keep_key

    def to_dict(self) -> dict[str, str]:
        """Serializes the alias table to a plain mapping.

        Returns:
            data: Alias-to-canonical mapping suitable for JSON output.
        """
        return dict(sorted(self.canonical_of.items()))


def save_alias_table(table: AliasTable, path: Path) -> None:
    """Persists an alias table to a JSON file.

    Args:
        table: Table to serialize.
        path: Destination file location.
    """
    path.write_text(json.dumps(table.to_dict(), indent=2) + "\n", encoding="utf-8")


def load_alias_table(path: Path) -> AliasTable:
    """Restores an alias table from a JSON file, tolerating absence.

    Args:
        path: File location to read; missing files yield an empty table.

    Returns:
        table: Restored table, or an empty one when the file is absent.
    """
    if not path.exists():
        return AliasTable()
    table = AliasTable()
    table.canonical_of = dict(json.loads(path.read_text(encoding="utf-8")))
    return table


@dataclass(frozen=True)
class ReviewItem:
    """Represents one borderline merge awaiting human judgement.

    Attributes:
        item_id: Stable identifier of the review item.
        canonical: Proposed canonical name.
        alias: Proposed alias to fold in.
        similarity: Embedding similarity that triggered the review.
        context: Short note on where the pair was observed.
    """

    item_id: str
    canonical: str
    alias: str
    similarity: float
    context: str = ""


@dataclass
class MergeReviewQueue:
    """Queues borderline merge candidates for human approval.

    Attributes:
        pending_items: Items awaiting a human decision, in arrival order.
        decided: Record of approvals and rejections already made.
    """

    pending_items: list[ReviewItem] = field(default_factory=list)
    decided: dict[str, bool] = field(default_factory=dict)

    def submit(self, item: ReviewItem) -> None:
        """Enqueues a borderline merge candidate for review.

        Args:
            item: Candidate to review; duplicates by id are ignored.
        """
        if any(existing.item_id == item.item_id for existing in self.pending_items):
            return
        if item.item_id in self.decided:
            return
        self.pending_items.append(item)

    def approve(self, item_id: str) -> ReviewItem:
        """Accepts a pending merge and removes it from the queue.

        Args:
            item_id: Identifier of the item being approved.

        Returns:
            item: The approved review item.
        """
        item = self._take(item_id)
        self.decided[item_id] = True
        return item

    def reject(self, item_id: str) -> ReviewItem:
        """Declines a pending merge and removes it from the queue.

        Args:
            item_id: Identifier of the item being rejected.

        Returns:
            item: The rejected review item.
        """
        item = self._take(item_id)
        self.decided[item_id] = False
        return item

    def _take(self, item_id: str) -> ReviewItem:
        """Pops a pending item from the queue by identifier.

        Args:
            item_id: Identifier of the item to remove.

        Returns:
            item: The removed review item.
        """
        for index, item in enumerate(self.pending_items):
            if item.item_id == item_id:
                return self.pending_items.pop(index)
        msg = f"no pending review item with id {item_id!r}"
        raise KeyError(msg)
