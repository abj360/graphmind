#!/usr/bin/env python3
"""
__init__.py --- Neo4j loading and incremental CDC ingestion

Contains:
    __all__: public surface of the load package
"""

from load.neo4j_loader import Neo4jLoader

__all__ = [
    "Neo4jLoader",
]
