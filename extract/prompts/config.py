#!/usr/bin/env python3
"""
config.py --- decoupled prompt configuration loading and validation

Contains:
    PromptConfig: rendering knobs decoupled from extraction logic
    DEFAULT_CONFIG_PATH: bundled prompt configuration file
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PromptConfig:
    """Carries prompt rendering choices independent of the extractor.

    Attributes:
        domain: Domain key selecting hints and few-shot examples.
        few_shot_count: Number of worked examples embedded in the prompt.
        require_citations: Whether prompts demand source-span citations.
        max_predicate_tokens: Soft cap on predicate phrase length.
        extra_instructions: Free-form lines appended to the rule block.
    """

    domain: str = "general"
    few_shot_count: int = 2
    require_citations: bool = False
    max_predicate_tokens: int = 5
    extra_instructions: tuple[str, ...] = ()


DEFAULT_CONFIG_PATH = Path(__file__).with_name("default.toml")
