#!/usr/bin/env python3
"""
cdc_poller.py --- change-data-capture polling for incremental corpus ingestion

Contains:
    logger
    ChangeKind: kinds of observed source changes
"""

import hashlib
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


class ChangeKind:
    """Enumerates the kinds of source document changes."""

    UPSERT = "upsert"
    DELETE = "delete"
