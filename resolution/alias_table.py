#!/usr/bin/env python3
"""
alias_table.py --- alias table and human-in-the-loop merge review queue

Contains:
    AliasTable: canonical name to known aliases mapping
    AliasTable.add(): registers one alias under a canonical name
    AliasTable.canonical_for(): resolves an alias to its canonical
    AliasTable.aliases(): lists aliases of a canonical name
    AliasTable._normalize(): shared key normalization
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
