#!/usr/bin/env python3
"""
templates.py --- prompt templates for SPO triple extraction across domains

Contains:
    SYSTEM_PROMPT: base instruction framing the extraction task
    EXTRACTION_RULES: hard output rules every prompt repeats
    format_rules(): renders the rule list as a numbered block
    build_extraction_prompt(): assembles the full prompt
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from extract.prompts.config import PromptConfig

SYSTEM_PROMPT = (
    "You are an information-extraction engine. Extract "
    "subject-predicate-object triples from the supplied text, covering every "
    "relationship the text mentions or implies."
)

EXTRACTION_RULES = [
    "Return a JSON array; each element is one triple.",
    "Each triple has subject, predicate, and object keys.",
    "Subjects and objects have name and entity_type keys.",
    "Predicates are short verb phrases, at most five tokens.",
    "Include a confidence score between 0.0 and 1.0 per triple.",
    "Do not emit duplicates or self-loops.",
]


def format_rules(rules: list[str]) -> str:
    """Renders extraction rules as a numbered prompt block.

    Args:
        rules: Rule strings to enumerate.

    Returns:
        block: Newline-joined numbered rules.
    """
    return "\n".join(f"{position}. {rule}" for position, rule in enumerate(rules, 1))


def build_extraction_prompt(text: str) -> str:
    """Assembles the full extraction prompt for one text window.

    Args:
        text: Text window the model should extract triples from.

    Returns:
        prompt: System prompt, rules, and the target text.
    """
    sections = [SYSTEM_PROMPT, format_rules(EXTRACTION_RULES)]
    sections.append(f"Text:\n{text}\n\nTriples JSON:")
    return "\n\n".join(sections)
