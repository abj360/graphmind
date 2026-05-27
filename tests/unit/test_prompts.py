#!/usr/bin/env python3
"""
test_prompts.py --- unit tests for extraction prompt templates and config

Contains:
"""

import pytest

from extract.prompts.config import PromptConfig, load_prompt_config, validate_prompt_config
from extract.prompts.templates import (
    DOMAIN_HINTS,
    EXTRACTION_RULES,
    SYSTEM_PROMPT,
    build_extraction_prompt,
    validate_domain,
)
