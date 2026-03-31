#!/usr/bin/env python3
"""
schema.py --- pydantic models and validation helpers for extracted SPO triples

Contains:
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
