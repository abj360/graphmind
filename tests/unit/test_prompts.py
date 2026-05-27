#!/usr/bin/env python3
"""
test_prompts.py --- unit tests for extraction prompt templates and config

Contains:
    test_prompt_contains_system_prompt_and_rules
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


def test_prompt_contains_system_prompt_and_rules() -> None:
    """Checks that a rendered prompt carries the system prompt and rules."""
    prompt = build_extraction_prompt("Alice founded Acme.")
    assert SYSTEM_PROMPT.split(".")[0] in prompt
    assert EXTRACTION_RULES[0] in prompt
    assert "Alice founded Acme." in prompt
