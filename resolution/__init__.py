#!/usr/bin/env python3
"""
__init__.py --- embedding-based entity resolution and alias management

Contains:
    __all__: public surface of the resolution package
"""

from resolution.alias_table import AliasTable
from resolution.entity_resolver import EntityResolver

__all__ = [
    "AliasTable",
    "EntityResolver",
]
