#!/usr/bin/env python3
"""
ontology.py --- ontology rules and schema enforcement for extracted triples

Contains:
"""

import json
from dataclasses import dataclass
from pathlib import Path

from extract.schema import Triple
