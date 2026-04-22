#!/usr/bin/env python3
"""
llm_client.py --- pluggable LLM client protocol used by the extraction pipeline

Contains:
    LLMClient: minimal completion protocol every provider implements
    FakeLLMClient: deterministic scripted client for tests
    FailingLLMClient: raises a configurable error for retry tests
    LangChainClient: adapts a LangChain chat model to LLMClient
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


class FailingLLMClient:
    """Fails a fixed number of times before delegating, for retry tests.

    Attributes:
        failures_remaining: How many calls still raise before succeeding.
        inner: Wrapped client that handles calls once failures run out.
    """

    def __init__(self, failures: int, inner: LLMClient) -> None:
        """Creates a flaky wrapper around a working client.

        Args:
            failures: Number of calls that should raise RuntimeError.
            inner: Client to delegate to once failures are exhausted.
        """
        self.failures_remaining = failures
        self.inner = inner

    def complete(self, prompt: str) -> str:
        """Raises while failures remain, otherwise delegates.

        Args:
            prompt: Rendered extraction prompt to complete.

        Returns:
            completion: Inner client's completion, once failures run out.
        """
        if self.failures_remaining > 0:
            self.failures_remaining -= 1
            raise RuntimeError("simulated transient LLM failure")
        return self.inner.complete(prompt)


class LangChainClient:
    """Adapts any LangChain chat model to the LLMClient protocol.

    Attributes:
        model: LangChain chat model instance used for completions.
    """

    def __init__(self, model: object) -> None:
        """Creates an adapter around a LangChain chat model.

        Args:
            model: Chat model exposing the LangChain invoke() interface.
        """
        self.model = model

    def complete(self, prompt: str) -> str:
        """Produces a completion by delegating to the wrapped chat model.

        Args:
            prompt: Rendered extraction prompt to complete.

        Returns:
            completion: Text content of the model's response message.
        """
        message = self.model.invoke(prompt)  # type: ignore[attr-defined]
        content = message.content
        return content if isinstance(content, str) else str(content)
