#!/usr/bin/env python3
"""
test_prompts.py --- unit tests for extraction prompt templates and config

Contains:
    test_prompt_contains_system_prompt_and_rules
    test_prompt_embeds_few_shot_examples
    test_domain_hint_rendered_for_known_domain
    test_validate_domain_rejects_unknown_keys
    test_load_prompt_config_reads_bundled_default
    test_load_prompt_config_reads_custom_file
    test_validate_prompt_config_rejects_bad_values
    test_citation_block_present_only_when_required
    test_config_from_dict_applies_overrides
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


def test_load_prompt_config_reads_custom_file(tmp_path) -> None:
    """Checks that a custom TOML config file overrides defaults."""
    config_path = tmp_path / "custom.toml"
    config_path.write_text('[prompts]\ndomain = "news"\nfew_shot_count = 3\n')
    config = load_prompt_config(config_path)
    assert config.domain == "news"
    assert config.few_shot_count == 3


def test_validate_prompt_config_rejects_bad_values() -> None:
    """Checks that negative few-shot counts are rejected."""
    with pytest.raises(ValueError):
        validate_prompt_config(PromptConfig(few_shot_count=-1))


def test_citation_block_present_only_when_required() -> None:
    """Checks that the citation block appears only when citations are on."""
    without = build_extraction_prompt("text", PromptConfig(require_citations=False))
    with_ = build_extraction_prompt("text", PromptConfig(require_citations=True))
    assert "source_span" not in without
    assert "source_span" in with_


def test_config_from_dict_applies_overrides() -> None:
    """Checks that config_from_dict maps plain data into a config."""
    from extract.prompts.config import config_from_dict

    config = config_from_dict({"domain": "news", "few_shot_count": 1})
    assert config.domain == "news"
    assert config.few_shot_count == 1
