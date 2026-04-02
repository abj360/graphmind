#!/usr/bin/env python3
"""
alias_table.py --- alias table and human-in-the-loop merge review queue

Contains:
    AliasTable: canonical name to known aliases mapping
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
