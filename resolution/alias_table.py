#!/usr/bin/env python3
"""
alias_table.py --- alias table and human-in-the-loop merge review queue

Contains:
    AliasTable: canonical name to known aliases mapping
    AliasTable.add(): registers one alias under a canonical name
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
