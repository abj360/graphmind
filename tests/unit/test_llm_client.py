#!/usr/bin/env python3
"""
test_llm_client.py --- unit tests for building the production LLM client

Contains:
    test_build_default_client_*: how the API key is resolved
"""

import pytest

from extract.llm_client import MissingAPIKeyError, build_default_client


def test_build_default_client_refuses_a_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies an unset key stops the run instead of calling the provider."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(MissingAPIKeyError, match="OPENAI_API_KEY"):
        build_default_client("gpt-4o-mini")


def test_build_default_client_refuses_an_empty_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies an empty key is treated as absent, not as a usable credential."""
    monkeypatch.setenv("OPENAI_API_KEY", "")
    with pytest.raises(MissingAPIKeyError):
        build_default_client("gpt-4o-mini")


def test_build_default_client_reads_the_named_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies the key comes from the environment, not from the variable name.

    The argument is the name of the variable holding the key; passing that name
    through as the key itself authenticates every request with the literal
    string "OPENAI_API_KEY".
    """
    monkeypatch.setenv("GRAPHMIND_TEST_KEY", "sk-real-value")
    client = build_default_client("gpt-4o-mini", api_key_env="GRAPHMIND_TEST_KEY")
    key = client.model.openai_api_key  # type: ignore[attr-defined]
    assert key.get_secret_value() == "sk-real-value"


def test_build_default_client_honours_a_custom_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies a non-default variable name is respected."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OTHER_PROVIDER_KEY", "sk-other")
    assert build_default_client("gpt-4o-mini", api_key_env="OTHER_PROVIDER_KEY") is not None
