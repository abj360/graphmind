#!/usr/bin/env python3
"""
test_prompts.py --- unit tests for extraction prompt templates and config

Contains:
    test_prompt_contains_system_prompt_and_rules
    test_prompt_embeds_few_shot_examples
    test_domain_hint_rendered_for_known_domain
    test_validate_domain_rejects_unknown_keys
    test_load_prompt_config_reads_bundled_default
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


def test_prompt_embeds_few_shot_examples() -> None:
    """Checks that few-shot examples appear in the rendered prompt."""
    prompt = build_extraction_prompt("text", PromptConfig(few_shot_count=1))
    assert "Example input:" in prompt


def test_domain_hint_rendered_for_known_domain() -> None:
    """Checks that known domains contribute their hint to the prompt."""
    prompt = build_extraction_prompt("text", PromptConfig(domain="technical"))
    assert DOMAIN_HINTS["technical"] in prompt


def test_validate_domain_rejects_unknown_keys() -> None:
    """Checks that unsupported domain keys are rejected with guidance."""
    with pytest.raises(ValueError):
        validate_domain("astrology")


def test_load_prompt_config_reads_bundled_default() -> None:
    """Checks that the bundled default config loads and validates."""
    config = load_prompt_config()
    assert config.domain == "general"
    assert config.few_shot_count >= 0
