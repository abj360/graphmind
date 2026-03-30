#!/usr/bin/env python3
"""
neo4j_loader.py --- batched, upsert-only writer loading triples into Neo4j

Contains:
    logger + query constants
"""

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Protocol

from extract.schema import Triple

logger = logging.getLogger(__name__)
