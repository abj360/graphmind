#!/usr/bin/env python3
"""
llm_client.py --- pluggable LLM client protocol used by the extraction pipeline

Contains:
    LLMClient: minimal completion protocol every provider implements
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    """Describes the completion interface the extractor depends on."""

    def complete(self, prompt: str) -> str:
        """Produces a raw completion for a fully-rendered prompt.

        Args:
            prompt: Rendered extraction prompt to complete.

        Returns:
            completion: Raw model output, expected to contain a JSON array.
        """
        ...
