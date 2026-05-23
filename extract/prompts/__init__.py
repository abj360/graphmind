#!/usr/bin/env python3
"""
__init__.py --- domain-specific extraction prompts and prompt configuration

Contains:
    __all__: public surface of the prompts package
"""

from extract.prompts.config import PromptConfig, load_prompt_config
from extract.prompts.templates import build_extraction_prompt

__all__ = [
    "PromptConfig",
    "build_extraction_prompt",
    "load_prompt_config",
]
