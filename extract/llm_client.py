#!/usr/bin/env python3
"""
llm_client.py --- pluggable LLM client protocol used by the extraction pipeline

Contains:
    LLMClient: minimal completion protocol every provider implements
    FakeLLMClient: deterministic scripted client for tests
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


class FakeLLMClient:
    """Returns scripted completions in order, for deterministic tests.

    Attributes:
        responses: Queue of completions handed out one per call.
        prompts: Every prompt received, recorded for assertions.
    """

    def __init__(self, responses: list[str]) -> None:
        """Creates a scripted client with a fixed response queue.

        Args:
            responses: Completions to hand out, in call order; the last
                one repeats if the queue runs dry.
        """
        self.responses = list(responses)
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        """Records the prompt and returns the next scripted completion.

        Args:
            prompt: Rendered extraction prompt to record.

        Returns:
            completion: Next scripted response from the queue.
        """
        self.prompts.append(prompt)
        if len(self.responses) > 1:
            return self.responses.pop(0)
        return self.responses[0]
