#!/usr/bin/env python3
"""
entity_resolver.py --- entity resolution via normalized string matching (naive, pre-embedding)

Contains:
    normalize_name(): folds an entity name to its comparison key
"""

import re
from dataclasses import dataclass

from extract.schema import Triple


def normalize_name(name: str) -> str:
    """Folds an entity name into a normalized comparison key.

    Args:
        name: Raw entity surface form.

    Returns:
        key: Lowercased, punctuation-stripped, whitespace-collapsed name.
    """
    stripped = re.sub(r"[^\w\s]", "", name)
    return " ".join(stripped.casefold().split())
