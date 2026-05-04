#!/usr/bin/env python3
"""
config.py --- decoupled prompt configuration loading and validation

Contains:
    PromptConfig: rendering knobs decoupled from extraction logic
    DEFAULT_CONFIG_PATH: bundled prompt configuration file
    load_prompt_config(): loads config from a TOML file
    validate_prompt_config(): rejects inconsistent prompt settings
    write_prompt_config(): persists a config back to TOML
    with_domain(): derives a config pinned to a domain
    describe_prompt_config(): one-line config summary
    config_from_dict(): builds a config from a plain mapping
    merge_configs(): overlays one config onto another
    diff_configs(): fields that differ between two configs
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


def load_prompt_config(path: Path | None = None) -> PromptConfig:
    """Loads prompt configuration from a TOML file.

    Args:
        path: Config file location; the bundled default is used when omitted.

    Returns:
        config: Validated prompt configuration.
    """
    source = path or DEFAULT_CONFIG_PATH
    with source.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("prompts", {})
    return validate_prompt_config(
        PromptConfig(
            domain=section.get("domain", "general"),
            few_shot_count=section.get("few_shot_count", 2),
            require_citations=section.get("require_citations", False),
            max_predicate_tokens=section.get("max_predicate_tokens", 5),
            extra_instructions=tuple(section.get("extra_instructions", ())),
        )
    )


def validate_prompt_config(config: PromptConfig) -> PromptConfig:
    """Rejects prompt configurations that cannot render sensibly.

    Args:
        config: Candidate prompt configuration.

    Returns:
        config: The same configuration, if valid.
    """
    if config.few_shot_count < 0:
        msg = f"few_shot_count {config.few_shot_count} must not be negative"
        raise ValueError(msg)
    if config.max_predicate_tokens < 1:
        msg = f"max_predicate_tokens {config.max_predicate_tokens} must be at least 1"
        raise ValueError(msg)
    return config


def write_prompt_config(config: PromptConfig, path: Path) -> None:
    """Persists a prompt configuration as a TOML file.

    Args:
        config: Configuration to serialize.
        path: Destination file location.
    """
    lines = [
        "[prompts]",
        f'domain = "{config.domain}"',
        f"few_shot_count = {config.few_shot_count}",
        f"require_citations = {'true' if config.require_citations else 'false'}",
        f"max_predicate_tokens = {config.max_predicate_tokens}",
    ]
    if config.extra_instructions:
        rendered = ", ".join(f'"{line}"' for line in config.extra_instructions)
        lines.append(f"extra_instructions = [{rendered}]")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def with_domain(config: PromptConfig, domain: str) -> PromptConfig:
    """Derives a copy of a prompt config pinned to one domain.

    Args:
        config: Base configuration to copy.
        domain: Domain key for the derived configuration.

    Returns:
        config: New configuration with the domain replaced.
    """
    from dataclasses import replace

    return replace(config, domain=domain)


def describe_prompt_config(config: PromptConfig) -> str:
    """Renders a prompt configuration as a log-friendly one-liner.

    Args:
        config: Configuration to summarize.

    Returns:
        summary: One-line rendering of the prompt knobs.
    """
    return (
        f"domain={config.domain} few_shot={config.few_shot_count} "
        f"citations={config.require_citations} "
        f"max_predicate_tokens={config.max_predicate_tokens}"
    )


def config_from_dict(data: dict[str, Any]) -> PromptConfig:  # Any: raw parsed config
    """Builds a validated prompt config from a plain mapping.

    Args:
        data: Mapping with optional prompt configuration keys.

    Returns:
        config: Validated prompt configuration.
    """
    return validate_prompt_config(
        PromptConfig(
            domain=str(data.get("domain", "general")),
            few_shot_count=int(data.get("few_shot_count", 2)),
            require_citations=bool(data.get("require_citations", False)),
            max_predicate_tokens=int(data.get("max_predicate_tokens", 5)),
            extra_instructions=tuple(data.get("extra_instructions", ())),
        )
    )


def merge_configs(base: PromptConfig, override: PromptConfig) -> PromptConfig:
    """Overlays a non-default config onto a base config.

    Args:
        base: Configuration providing fallback values.
        override: Configuration whose non-default fields win.

    Returns:
        config: Merged configuration, validated.
    """
    from dataclasses import replace

    default = PromptConfig()
    changes = {
        field: getattr(override, field)
        for field in ("domain", "few_shot_count", "require_citations", "max_predicate_tokens")
        if getattr(override, field) != getattr(default, field)
    }
    return validate_prompt_config(replace(base, **changes))


def diff_configs(left: PromptConfig, right: PromptConfig) -> dict[str, tuple[object, object]]:
    """Reports the fields on which two prompt configs differ.

    Args:
        left: First configuration.
        right: Second configuration.

    Returns:
        diff: Mapping of field name to (left, right) values that differ.
    """
    diff: dict[str, tuple[object, object]] = {}
    for field in ("domain", "few_shot_count", "require_citations", "max_predicate_tokens"):
        if getattr(left, field) != getattr(right, field):
            diff[field] = (getattr(left, field), getattr(right, field))
    return diff
